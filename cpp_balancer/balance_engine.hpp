#ifndef BALANCE_ENGINE_HPP
#define BALANCE_ENGINE_HPP

#include <vector>
#include <string>
#include <unordered_map>
#include <optional>
#include <algorithm>
#include <cmath>
#include <numeric>
#include <thread>
#include <mutex>
#include <atomic>
#include <future>

// ==================== Data Structures ====================

struct RoleRating {
    int role_id;
    int rating;
    int priority;
};

struct PlayerInfo {
    int member_id;
    std::vector<RoleRating> roles;
    
    bool can_play_role(int role_id) const {
        for (const auto& r : roles) {
            if (r.role_id == role_id) return true;
        }
        return false;
    }
    
    int get_rating_for_role(int role_id) const {
        for (const auto& r : roles) {
            if (r.role_id == role_id) return r.rating;
        }
        return 0;
    }
    
    int get_priority_for_role(int role_id) const {
        for (const auto& r : roles) {
            if (r.role_id == role_id) return r.priority;
        }
        return 0;
    }
};

struct RoleConstraint {
    int min_in_team;
    int max_in_team;
};

struct QualitySettings {
    float alpha = 1.0f;
    float beta = 1.0f;
    float gamma = 1.0f;
    float p = 1.0f;
    float q = 1.0f;
    float g = 1.0f;
    int max_priority = 3;
    std::unordered_map<int, float> role_weights;
};

struct QualityMetrics {
    float fairness = 0.0f;
    float role_fairness = 0.0f;
    float role_points = 0.0f;
    float uniformity = 0.0f;
    
    float total() const {
        return fairness + role_fairness + role_points + uniformity;
    }
};

struct TeamPlayerResult {
    int member_id;
    int role_id;
    int rating;
};

struct TeamResult {
    std::string name;
    std::vector<TeamPlayerResult> players;
};

struct BalanceResultData {
    QualityMetrics quality;
    std::vector<TeamResult> teams;
    std::string team_mask;
    std::string role_mask1;
    std::string role_mask2;
};

struct BalanceResponse {
    int result_code = 200;
    std::string status = "ok";
    std::vector<BalanceResultData> balances;
};

// ==================== Per-Worker Context ====================
// Каждый воркер получает свой набор буферов — никаких блокировок в hot path

struct WorkerContext {
    struct TeamBuffers {
        std::vector<const PlayerInfo*> players;
        std::vector<int> ratings;
        std::vector<int> role_indices;
        std::vector<int> actual_role_ids;
        
        void resize(int size) {
            players.resize(size);
            ratings.resize(size);
            role_indices.resize(size);
            actual_role_ids.resize(size);
        }
    };
    
    TeamBuffers team1_buf;
    TeamBuffers team2_buf;
    std::vector<const std::vector<int>*> valid_masks1;
    std::vector<const std::vector<int>*> valid_masks2;
    
    // Локальные результаты воркера — без синхронизации
    std::vector<BalanceResultData> local_results;
    
    // Флаги для error tracking
    bool any_mask_valid = false;
    bool any_balance_valid = false;
    
    void init(int team_size, size_t role_masks_count) {
        team1_buf.resize(team_size);
        team2_buf.resize(team_size);
        valid_masks1.reserve(role_masks_count);
        valid_masks2.reserve(role_masks_count);
        local_results.reserve(1024);
    }
};

// ==================== Main Engine ====================

class BalanceEngine {
public:
    BalanceEngine(const QualitySettings& settings, 
                  const std::vector<int>& role_ids,
                  const std::unordered_map<int, RoleConstraint>& constraints,
                  int num_workers = 0);  // 0 = auto-detect
    
    BalanceResponse find_balances(
        const std::vector<PlayerInfo>& players,
        int team_size,
        float balance_limit,
        int max_results = 1000
    );

private:
    QualitySettings settings_;
    std::vector<int> role_ids_;
    std::unordered_map<int, RoleConstraint> constraints_;
    int num_workers_;
    
    // Pre-generated masks (shared read-only across workers)
    std::vector<std::vector<int>> role_masks_;
    
    // Mask generation
    void generate_role_masks(int team_size);
    static std::vector<std::vector<int>> generate_team_masks(int total, int team_size);
    
    // Validation
    bool is_mask_valid(const std::vector<const PlayerInfo*>& team,
                       const std::vector<int>& mask) const;
    
    // Direct assignment
    void apply_mask(const std::vector<const PlayerInfo*>& team,
                    const std::vector<int>& mask,
                    std::vector<int>& ratings,
                    std::vector<int>& actual_role_ids) const;
    
    // Quality calculations (все const — безопасны для параллельного вызова)
    float calc_fairness(const std::vector<int>& r1, const std::vector<int>& r2) const;
    float calc_uniformity(const std::vector<int>& r1, const std::vector<int>& r2) const;
    float calc_role_fairness(const std::vector<int>& r1, const std::vector<int>& r2,
                             const std::vector<int>& m1, const std::vector<int>& m2) const;
    float calc_role_points(const std::vector<const PlayerInfo*>& t1,
                           const std::vector<const PlayerInfo*>& t2,
                           const std::vector<int>& roles1,
                           const std::vector<int>& roles2) const;
    
    // Worker function — обрабатывает диапазон team_masks
    void worker_process(
        WorkerContext& ctx,
        const std::vector<PlayerInfo>& players,
        const std::vector<std::vector<int>>& team_masks,
        size_t begin_idx,
        size_t end_idx,
        int team_size,
        float balance_limit
    );
    
    static std::string mask_to_string(const std::vector<int>& mask);
};

#endif