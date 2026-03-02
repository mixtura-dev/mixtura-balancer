#include "balance_engine.hpp"
#include <functional>

// ==================== Constructor ====================

BalanceEngine::BalanceEngine(
    const QualitySettings& settings,
    const std::vector<int>& role_ids,
    const std::unordered_map<int, RoleConstraint>& constraints
) : settings_(settings), role_ids_(role_ids), constraints_(constraints) {}

// ==================== Mask Generation ====================

std::vector<std::vector<int>> BalanceEngine::generate_team_masks(int total, int team_size) {
    std::vector<std::vector<int>> masks;
    
    // Use selector pattern for combination generation
    std::vector<bool> selector(total, false);
    std::fill(selector.begin(), selector.begin() + team_size, true);
    
    do {
        std::vector<int> mask(total);
        for (int i = 0; i < total; ++i) {
            mask[i] = selector[i] ? 0 : 1;
        }
        masks.push_back(std::move(mask));
    } while (std::prev_permutation(selector.begin(), selector.end()));
    
    return masks;
}

void BalanceEngine::generate_role_masks(int team_size) {
    role_masks_.clear();
    
    int num_roles = role_ids_.size();
    std::vector<int> current(team_size);
    std::vector<int> counts(num_roles, 0);
    
    // Get max constraints for each role
    std::vector<int> max_per_role(num_roles, team_size);
    std::vector<int> min_per_role(num_roles, 0);
    
    for (int i = 0; i < num_roles; ++i) {
        auto it = constraints_.find(role_ids_[i]);
        if (it != constraints_.end()) {
            max_per_role[i] = it->second.max_in_team;
            min_per_role[i] = it->second.min_in_team;
        }
    }
    
    // Recursive generation with constraint checking
    std::function<void(int)> generate = [&](int pos) {
        if (pos == team_size) {
            // Verify minimum requirements
            for (int i = 0; i < num_roles; ++i) {
                if (counts[i] < min_per_role[i]) return;
            }
            role_masks_.push_back(current);
            return;
        }
        
        for (int role_idx = 0; role_idx < num_roles; ++role_idx) {
            if (counts[role_idx] < max_per_role[role_idx]) {
                current[pos] = role_idx;
                counts[role_idx]++;
                generate(pos + 1);
                counts[role_idx]--;
            }
        }
    };
    
    generate(0);
}

// ==================== Validation (KEY OPTIMIZATION) ====================

bool BalanceEngine::is_mask_valid(
    const std::vector<const PlayerInfo*>& team,
    const std::vector<int>& mask
) const {
    // Simple O(n) check - no backtracking!
    // Position i in mask directly maps to player i
    for (size_t i = 0; i < team.size(); ++i) {
        
        int role_id = role_ids_[mask[i]];
        if (!team[i]->can_play_role(role_id)) {
            return false;
        }
    }
    return true;
}

// ==================== Direct Assignment (KEY OPTIMIZATION) ====================

void BalanceEngine::apply_mask(
    const std::vector<const PlayerInfo*>& team,
    const std::vector<int>& mask,
    std::vector<int>& ratings,
    std::vector<int>& actual_role_ids
) {
    // O(n) direct assignment - mask[i] tells us exactly which role player i gets
    for (size_t i = 0; i < team.size(); ++i) {
        int role_id = role_ids_[mask[i]];
        actual_role_ids[i] = role_id;
        ratings[i] = team[i]->get_rating_for_role(role_id);
    }
}

// ==================== Quality Calculations ====================

float BalanceEngine::calc_fairness(
    const std::vector<int>& r1, 
    const std::vector<int>& r2
) const {
    float p = settings_.p;
    float sum1 = 0.0f, sum2 = 0.0f;
    
    for (int r : r1) sum1 += std::pow(static_cast<float>(r), p);
    for (int r : r2) sum2 += std::pow(static_cast<float>(r), p);
    
    return settings_.alpha * std::abs(
        std::pow(sum1, 1.0f / p) - std::pow(sum2, 1.0f / p)
    );
}

float BalanceEngine::calc_uniformity(
    const std::vector<int>& r1, 
    const std::vector<int>& r2
) const {
    size_t total = r1.size() + r2.size();
    if (total == 0) return 0.0f;
    
    float mean = 0.0f;
    for (int r : r1) mean += r;
    for (int r : r2) mean += r;
    mean /= total;
    
    float q = settings_.q;
    float dev1 = 0.0f, dev2 = 0.0f;
    
    for (int r : r1) dev1 += std::pow(std::abs(r - mean), q);
    for (int r : r2) dev2 += std::pow(std::abs(r - mean), q);
    
    dev1 = r1.empty() ? 0.0f : std::pow(dev1 / r1.size(), 1.0f / q);
    dev2 = r2.empty() ? 0.0f : std::pow(dev2 / r2.size(), 1.0f / q);
    
    return std::abs(dev1 - dev2);
}

float BalanceEngine::calc_role_fairness(
    const std::vector<int>& r1, const std::vector<int>& r2,
    const std::vector<int>& m1, const std::vector<int>& m2
) const {
    int num_roles = role_ids_.size();
    std::vector<int> sums1(num_roles, 0), sums2(num_roles, 0);
    
    for (size_t i = 0; i < r1.size(); ++i) sums1[m1[i]] += r1[i];
    for (size_t i = 0; i < r2.size(); ++i) sums2[m2[i]] += r2[i];
    
    float g = settings_.g;
    float weighted_sum = 0.0f;
    
    for (int i = 0; i < num_roles; ++i) {
        float weight = 1.0f;
        auto it = settings_.role_weights.find(role_ids_[i]);
        if (it != settings_.role_weights.end()) {
            weight = it->second;
        }
        
        float diff = std::abs(static_cast<float>(sums1[i] - sums2[i]));
        weighted_sum += std::pow(diff * weight, g);
    }
    
    return settings_.beta * std::pow(weighted_sum / num_roles, 1.0f / g);
}

float BalanceEngine::calc_role_points(
    const std::vector<const PlayerInfo*>& t1,
    const std::vector<const PlayerInfo*>& t2,
    const std::vector<int>& roles1,
    const std::vector<int>& roles2
) const {
    int max_prio = settings_.max_priority;
    int total_players = t1.size() + t2.size();
    int total_points = total_players * max_prio;
    
    int team1_points = t1.size() * max_prio;
    int team2_points = t2.size() * max_prio;
    
    for (size_t i = 0; i < t1.size(); ++i) {
        int pts = t1[i]->get_priority_for_role(roles1[i]);
        total_points -= pts;
        team1_points -= pts;
    }
    
    for (size_t i = 0; i < t2.size(); ++i) {
        int pts = t2[i]->get_priority_for_role(roles2[i]);
        total_points -= pts;
        team2_points -= pts;
    }
    
    // Penalty for team imbalance
    int imbalance = std::abs(team1_points - team2_points);
    if (imbalance > 1) {
        total_points += static_cast<int>(0.2f * imbalance);
    }
    
    return settings_.gamma * total_points;
}

// ==================== Utility ====================

std::string BalanceEngine::mask_to_string(const std::vector<int>& mask) {
    std::string result;
    result.reserve(mask.size());
    for (int v : mask) {
        result += static_cast<char>('0' + v);
    }
    return result;
}

// ==================== Main Algorithm ====================

BalanceResponse BalanceEngine::find_balances(
    const std::vector<PlayerInfo>& players,
    int team_size,
    float balance_limit,
    int max_results
) {
    BalanceResponse response;
    
    // Validation
    if (static_cast<int>(players.size()) != team_size * 2) {
        response.result_code = 500;
        response.status = "Not enough players in lobby";
        return response;
    }
    
    // Pre-generate masks (done once)
    auto team_masks = generate_team_masks(players.size(), team_size);
    generate_role_masks(team_size);
    
    if (role_masks_.empty()) {
        response.result_code = 500;
        response.status = "Cannot generate valid role masks for constraints";
        return response;
    }
    
    // Pre-allocate reusable buffers
    team1_buf_.resize(team_size);
    team2_buf_.resize(team_size);
    valid_masks1_.reserve(role_masks_.size());
    valid_masks2_.reserve(role_masks_.size());
    
    bool any_mask_valid = false;
    bool any_balance_valid = false;
    
    // Main search loop
    for (const auto& team_mask : team_masks) {
        // Split players into teams using pointers (no copying!)
        int idx1 = 0, idx2 = 0;
        for (size_t i = 0; i < team_mask.size(); ++i) {
            if (team_mask[i] == 0) {
                team1_buf_.players[idx1++] = &players[i];
            } else {
                team2_buf_.players[idx2++] = &players[i];
            }
        }
        
        // ========== KEY OPTIMIZATION: Pre-filter valid masks ==========
        valid_masks1_.clear();
        valid_masks2_.clear();
        
        for (const auto& role_mask : role_masks_) {
            if (is_mask_valid(team1_buf_.players, role_mask)) {
                valid_masks1_.push_back(&role_mask);
            }
            if (is_mask_valid(team2_buf_.players, role_mask)) {
                valid_masks2_.push_back(&role_mask);
            }
        }
        
        // Track errors
        if (!valid_masks1_.empty() && !valid_masks2_.empty()) {
            any_mask_valid = true;
        } else {
            continue;  // Skip this team split
        }
        
        // ========== Only iterate valid combinations ==========
        for (const auto* mask1_ptr : valid_masks1_) {
            const auto& mask1 = *mask1_ptr;
            
            // Direct O(n) assignment for team 1
            apply_mask(team1_buf_.players, mask1, 
                      team1_buf_.ratings, team1_buf_.actual_role_ids);
            
            for (const auto* mask2_ptr : valid_masks2_) {
                const auto& mask2 = *mask2_ptr;
                
                // Direct O(n) assignment for team 2
                apply_mask(team2_buf_.players, mask2,
                          team2_buf_.ratings, team2_buf_.actual_role_ids);
                
                // Calculate quality metrics
                QualityMetrics quality;
                quality.fairness = calc_fairness(
                    team1_buf_.ratings, team2_buf_.ratings);
                quality.role_fairness = calc_role_fairness(
                    team1_buf_.ratings, team2_buf_.ratings, mask1, mask2);
                quality.role_points = calc_role_points(
                    team1_buf_.players, team2_buf_.players,
                    team1_buf_.actual_role_ids, team2_buf_.actual_role_ids);
                quality.uniformity = calc_uniformity(
                    team1_buf_.ratings, team2_buf_.ratings);
                
                float total = quality.total();
                
                // Early exit if over limit
                if (total > balance_limit) {
                    continue;
                }
                
                any_balance_valid = true;
                
                // Build result (only for valid balances)
                BalanceResultData result;
                result.quality = quality;
                result.team_mask = mask_to_string(team_mask);
                result.role_mask1 = mask_to_string(mask1);
                result.role_mask2 = mask_to_string(mask2);
                
                // Team 1
                TeamResult team1_result;
                team1_result.name = "team_1";
                team1_result.players.reserve(team_size);
                for (int i = 0; i < team_size; ++i) {
                    team1_result.players.push_back({
                        team1_buf_.players[i]->member_id,
                        team1_buf_.actual_role_ids[i],
                        team1_buf_.ratings[i]
                    });
                }
                
                // Team 2
                TeamResult team2_result;
                team2_result.name = "team_2";
                team2_result.players.reserve(team_size);
                for (int i = 0; i < team_size; ++i) {
                    team2_result.players.push_back({
                        team2_buf_.players[i]->member_id,
                        team2_buf_.actual_role_ids[i],
                        team2_buf_.ratings[i]
                    });
                }
                
                result.teams = {std::move(team1_result), std::move(team2_result)};
                response.balances.push_back(std::move(result));
            }
        }
    }
    
    // Handle errors
    if (!any_mask_valid) {
        response.result_code = 500;
        response.status = "Not enough players for each role";
        return response;
    }
    
    if (!any_balance_valid) {
        response.result_code = 500;
        response.status = "Can't shuffle players within balance limit";
        return response;
    }
    
    // Sort by quality and limit results
    std::sort(response.balances.begin(), response.balances.end(),
              [](const BalanceResultData& a, const BalanceResultData& b) {
                  return a.quality.total() < b.quality.total();
              });
    
    if (static_cast<int>(response.balances.size()) > max_results) {
        response.balances.resize(max_results);
    }
    
    return response;
}