#include "balance_engine.hpp"
#include <functional>

// ==================== Constructor ====================

BalanceEngine::BalanceEngine(
    const QualitySettings& settings,
    const std::vector<int>& role_ids,
    const std::unordered_map<int, RoleConstraint>& constraints,
    int num_workers
) : settings_(settings), role_ids_(role_ids), constraints_(constraints) {
    if (num_workers <= 0) {
        num_workers_ = static_cast<int>(std::thread::hardware_concurrency());
        if (num_workers_ <= 0) num_workers_ = 4;  // fallback
    } else {
        num_workers_ = num_workers;
    }
}

// ==================== Mask Generation ====================

std::vector<std::vector<int>> BalanceEngine::generate_team_masks(int total, int team_size) {
    std::vector<std::vector<int>> masks;
    
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
    
    std::vector<int> max_per_role(num_roles, team_size);
    std::vector<int> min_per_role(num_roles, 0);
    
    for (int i = 0; i < num_roles; ++i) {
        auto it = constraints_.find(role_ids_[i]);
        if (it != constraints_.end()) {
            max_per_role[i] = it->second.max_in_team;
            min_per_role[i] = it->second.min_in_team;
        }
    }
    
    std::function<void(int)> generate = [&](int pos) {
        if (pos == team_size) {
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

// ==================== Validation ====================

bool BalanceEngine::is_mask_valid(
    const std::vector<const PlayerInfo*>& team,
    const std::vector<int>& mask
) const {
    for (size_t i = 0; i < team.size(); ++i) {
        int role_id = role_ids_[mask[i]];
        if (!team[i]->can_play_role(role_id)) {
            return false;
        }
    }
    return true;
}

// ==================== Direct Assignment ====================

void BalanceEngine::apply_mask(
    const std::vector<const PlayerInfo*>& team,
    const std::vector<int>& mask,
    std::vector<int>& ratings,
    std::vector<int>& actual_role_ids
) const {
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
    
    int imbalance = std::abs(team1_points - team2_points);
    if (imbalance > 1) {
        total_points += static_cast<int>(settings_.xi * imbalance);
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

// ==================== Worker Function ====================
// Каждый воркер обрабатывает свой slice team_masks[begin_idx..end_idx)
// Полностью независимо, без блокировок, пишет только в свой WorkerContext

void BalanceEngine::worker_process(
    WorkerContext& ctx,
    const std::vector<PlayerInfo>& players,
    const std::vector<std::vector<int>>& team_masks,
    size_t begin_idx,
    size_t end_idx,
    int team_size,
    float balance_limit
) {
    for (size_t tm_idx = begin_idx; tm_idx < end_idx; ++tm_idx) {
        const auto& team_mask = team_masks[tm_idx];
        
        // Split players into teams
        int idx1 = 0, idx2 = 0;
        for (size_t i = 0; i < team_mask.size(); ++i) {
            if (team_mask[i] == 0) {
                ctx.team1_buf.players[idx1++] = &players[i];
            } else {
                ctx.team2_buf.players[idx2++] = &players[i];
            }
        }
        
        // Pre-filter valid role masks for each team
        ctx.valid_masks1.clear();
        ctx.valid_masks2.clear();
        
        for (const auto& role_mask : role_masks_) {
            if (is_mask_valid(ctx.team1_buf.players, role_mask)) {
                ctx.valid_masks1.push_back(&role_mask);
            }
            if (is_mask_valid(ctx.team2_buf.players, role_mask)) {
                ctx.valid_masks2.push_back(&role_mask);
            }
        }
        
        if (!ctx.valid_masks1.empty() && !ctx.valid_masks2.empty()) {
            ctx.any_mask_valid = true;
        } else {
            continue;
        }
        
        // Iterate valid combinations
        for (const auto* mask1_ptr : ctx.valid_masks1) {
            const auto& mask1 = *mask1_ptr;
            
            apply_mask(ctx.team1_buf.players, mask1,
                      ctx.team1_buf.ratings, ctx.team1_buf.actual_role_ids);
            
            for (const auto* mask2_ptr : ctx.valid_masks2) {
                const auto& mask2 = *mask2_ptr;
                
                apply_mask(ctx.team2_buf.players, mask2,
                          ctx.team2_buf.ratings, ctx.team2_buf.actual_role_ids);
                
                // Calculate quality
                QualityMetrics quality;
                quality.fairness = calc_fairness(
                    ctx.team1_buf.ratings, ctx.team2_buf.ratings);
                quality.role_fairness = calc_role_fairness(
                    ctx.team1_buf.ratings, ctx.team2_buf.ratings, mask1, mask2);
                quality.role_points = calc_role_points(
                    ctx.team1_buf.players, ctx.team2_buf.players,
                    ctx.team1_buf.actual_role_ids, ctx.team2_buf.actual_role_ids);
                quality.uniformity = calc_uniformity(
                    ctx.team1_buf.ratings, ctx.team2_buf.ratings);
                
                float total = quality.total();
                
                if (total > balance_limit) {
                    continue;
                }
                
                ctx.any_balance_valid = true;
                
                // Build result
                BalanceResultData result;
                result.quality = quality;
                result.team_mask = mask_to_string(team_mask);
                result.role_mask1 = mask_to_string(mask1);
                result.role_mask2 = mask_to_string(mask2);
                
                TeamResult team1_result;
                team1_result.name = "team_1";
                team1_result.players.reserve(team_size);
                for (int i = 0; i < team_size; ++i) {
                    team1_result.players.push_back({
                        ctx.team1_buf.players[i]->member_id,
                        ctx.team1_buf.actual_role_ids[i],
                        ctx.team1_buf.ratings[i]
                    });
                }
                
                TeamResult team2_result;
                team2_result.name = "team_2";
                team2_result.players.reserve(team_size);
                for (int i = 0; i < team_size; ++i) {
                    team2_result.players.push_back({
                        ctx.team2_buf.players[i]->member_id,
                        ctx.team2_buf.actual_role_ids[i],
                        ctx.team2_buf.ratings[i]
                    });
                }
                
                result.teams = {std::move(team1_result), std::move(team2_result)};
                ctx.local_results.push_back(std::move(result));
            }
        }
    }
}

// ==================== Main Algorithm (Parallel) ====================

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
    
    // Pre-generate masks (done once, before threading)
    auto team_masks = generate_team_masks(players.size(), team_size);
    generate_role_masks(team_size);
    
    if (role_masks_.empty()) {
        response.result_code = 500;
        response.status = "Cannot generate valid role masks for constraints";
        return response;
    }
    
    // ========== Determine actual worker count ==========
    size_t total_masks = team_masks.size();
    int actual_workers = std::min(
        num_workers_,
        static_cast<int>(total_masks)
    );
    
    // Для тривиальных случаев — однопоточно
    if (actual_workers <= 1) {
        actual_workers = 1;
    }
    
    // ========== Create per-worker contexts ==========
    std::vector<WorkerContext> contexts(actual_workers);
    for (auto& ctx : contexts) {
        ctx.init(team_size, role_masks_.size());
    }
    
    // ========== Partition team_masks across workers ==========
    // Равномерное распределение: chunk_size + remainder в последний воркер
    size_t chunk_size = total_masks / actual_workers;
    size_t remainder = total_masks % actual_workers;
    
    // ========== Launch worker threads ==========
    std::vector<std::thread> threads;
    threads.reserve(actual_workers - 1);
    
    size_t offset = 0;
    for (int w = 0; w < actual_workers; ++w) {
        // Распределяем remainder по первым воркерам (по 1 extra)
        size_t this_chunk = chunk_size + (w < static_cast<int>(remainder) ? 1 : 0);
        size_t begin_idx = offset;
        size_t end_idx = offset + this_chunk;
        offset = end_idx;
        
        if (w < actual_workers - 1) {
            // Запускаем в отдельном потоке
            threads.emplace_back(
                &BalanceEngine::worker_process, this,
                std::ref(contexts[w]),
                std::cref(players),
                std::cref(team_masks),
                begin_idx, end_idx,
                team_size, balance_limit
            );
        } else {
            // Последний chunk — в текущем потоке (избегаем лишний thread)
            worker_process(
                contexts[w], players, team_masks,
                begin_idx, end_idx,
                team_size, balance_limit
            );
        }
    }
    
    // ========== Join all threads ==========
    for (auto& t : threads) {
        t.join();
    }
    
    // ========== Merge results ==========
    bool any_mask_valid = false;
    bool any_balance_valid = false;
    
    // Подсчитаем общий размер для pre-allocation
    size_t total_results = 0;
    for (const auto& ctx : contexts) {
        total_results += ctx.local_results.size();
        any_mask_valid |= ctx.any_mask_valid;
        any_balance_valid |= ctx.any_balance_valid;
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
    
    // Merge all local results into response
    response.balances.reserve(total_results);
    for (auto& ctx : contexts) {
        // Move-append из каждого воркера
        response.balances.insert(
            response.balances.end(),
            std::make_move_iterator(ctx.local_results.begin()),
            std::make_move_iterator(ctx.local_results.end())
        );
    }
    
    // ========== Sort by quality and limit ==========
    // Для очень большого числа результатов — partial_sort эффективнее
    if (static_cast<int>(response.balances.size()) > max_results) {
        std::partial_sort(
            response.balances.begin(),
            response.balances.begin() + max_results,
            response.balances.end(),
            [](const BalanceResultData& a, const BalanceResultData& b) {
                return a.quality.total() < b.quality.total();
            }
        );
        response.balances.resize(max_results);
    } else {
        std::sort(
            response.balances.begin(), response.balances.end(),
            [](const BalanceResultData& a, const BalanceResultData& b) {
                return a.quality.total() < b.quality.total();
            }
        );
    }
    
    return response;
}