#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include "balance_engine.hpp"

namespace py = pybind11;

PYBIND11_MODULE(_core, m)
{
    m.doc() = "Balance Engine - optimized team balancing module";

    // ==================== RoleRating (было PlayerRoleInfo) ====================
    py::class_<RoleRating>(m, "RoleRating")
        .def(py::init<>())
        .def(py::init([](int role_id, int rating, int priority) {
            return RoleRating{role_id, rating, priority};
        }), py::arg("role_id"), py::arg("rating"), py::arg("priority"))
        .def_readwrite("role_id", &RoleRating::role_id)
        .def_readwrite("rating", &RoleRating::rating)
        .def_readwrite("priority", &RoleRating::priority)
        .def("__repr__", [](const RoleRating& r) {
            return "RoleRating(role_id=" + std::to_string(r.role_id) + 
                   ", rating=" + std::to_string(r.rating) + 
                   ", priority=" + std::to_string(r.priority) + ")";
        });

    // ==================== PlayerInfo ====================
    py::class_<PlayerInfo>(m, "PlayerInfo")
        .def(py::init<>())
        .def(py::init([](int member_id, const std::vector<RoleRating>& roles) {
            PlayerInfo p;
            p.member_id = member_id;
            p.roles = roles;
            return p;
        }), py::arg("member_id"), py::arg("roles"))
        .def_readwrite("member_id", &PlayerInfo::member_id)
        .def_readwrite("roles", &PlayerInfo::roles)
        .def("can_play_role", &PlayerInfo::can_play_role, py::arg("role_id"))
        .def("get_rating_for_role", &PlayerInfo::get_rating_for_role, py::arg("role_id"))
        .def("get_priority_for_role", &PlayerInfo::get_priority_for_role, py::arg("role_id"))
        .def("__repr__", [](const PlayerInfo& p) {
            return "PlayerInfo(member_id=" + std::to_string(p.member_id) + 
                   ", roles=[" + std::to_string(p.roles.size()) + " roles]" +
                   ")";
        });

    // ==================== RoleConstraint ====================
    py::class_<RoleConstraint>(m, "RoleConstraint")
        .def(py::init<>())
        .def(py::init([](int min_in_team, int max_in_team) {
            return RoleConstraint{min_in_team, max_in_team};
        }), py::arg("min_in_team"), py::arg("max_in_team"))
        .def_readwrite("min_in_team", &RoleConstraint::min_in_team)
        .def_readwrite("max_in_team", &RoleConstraint::max_in_team)
        .def("__repr__", [](const RoleConstraint& c) {
            return "RoleConstraint(min=" + std::to_string(c.min_in_team) + 
                   ", max=" + std::to_string(c.max_in_team) + ")";
        });

    // ==================== QualitySettings ====================
    py::class_<QualitySettings>(m, "QualitySettings")
        .def(py::init<>())
        .def_readwrite("alpha", &QualitySettings::alpha,
            "Weight for fairness metric")
        .def_readwrite("beta", &QualitySettings::beta,
            "Weight for role fairness metric")
        .def_readwrite("gamma", &QualitySettings::gamma,
            "Weight for role priority metric")
        .def_readwrite("p", &QualitySettings::p,
            "Power for fairness norm calculation")
        .def_readwrite("q", &QualitySettings::q,
            "Power for uniformity norm calculation")
        .def_readwrite("g", &QualitySettings::g,
            "Power for role fairness norm calculation")
        .def_readwrite("max_priority", &QualitySettings::max_priority,
            "Maximum role priority value")
        .def_readwrite("role_weights", &QualitySettings::role_weights,
            "Weight multipliers for each role (role_id -> weight)")
        .def("__repr__", [](const QualitySettings& s) {
            return "QualitySettings(alpha=" + std::to_string(s.alpha) +
                   ", beta=" + std::to_string(s.beta) +
                   ", gamma=" + std::to_string(s.gamma) + ")";
        });

    // ==================== QualityMetrics ====================
    py::class_<QualityMetrics>(m, "QualityMetrics")
        .def(py::init<>())
        .def(py::init([](float fairness, float role_fairness, float role_points, float uniformity) {
            return QualityMetrics{fairness, role_fairness, role_points, uniformity};
        }), py::arg("fairness"), py::arg("role_fairness"), 
           py::arg("role_points"), py::arg("uniformity"))
        .def_readwrite("fairness", &QualityMetrics::fairness,
            "Team skill fairness score")
        .def_readwrite("role_fairness", &QualityMetrics::role_fairness,
            "Role-based fairness score")
        .def_readwrite("role_points", &QualityMetrics::role_points,
            "Role priority satisfaction score")
        .def_readwrite("uniformity", &QualityMetrics::uniformity,
            "Skill distribution uniformity score")
        .def("total", &QualityMetrics::total,
            "Calculate total quality score (lower is better)")
        .def_property_readonly("total_score", &QualityMetrics::total,
            "Alias for total() for backwards compatibility")
        .def("__repr__", [](const QualityMetrics& q) {
            return "QualityMetrics(total=" + std::to_string(q.total()) +
                   ", fairness=" + std::to_string(q.fairness) +
                   ", role_fairness=" + std::to_string(q.role_fairness) +
                   ", role_points=" + std::to_string(q.role_points) +
                   ", uniformity=" + std::to_string(q.uniformity) + ")";
        });

    // ==================== TeamPlayerResult ====================
    py::class_<TeamPlayerResult>(m, "TeamPlayerResult")
        .def(py::init<>())
        .def(py::init([](int member_id, int role_id, int rating) {
            return TeamPlayerResult{member_id, role_id, rating};
        }), py::arg("member_id"), py::arg("role_id"), py::arg("rating"))
        .def_readwrite("member_id", &TeamPlayerResult::member_id)
        .def_readwrite("role_id", &TeamPlayerResult::role_id)
        .def_readwrite("rating", &TeamPlayerResult::rating)
        // Backwards compatibility aliases
        .def_property("game_role_id",
            [](const TeamPlayerResult& t) { return t.role_id; },
            [](TeamPlayerResult& t, int v) { t.role_id = v; },
            "Alias for role_id (backwards compatibility)")
        .def("__repr__", [](const TeamPlayerResult& t) {
            return "TeamPlayerResult(member_id=" + std::to_string(t.member_id) +
                   ", role_id=" + std::to_string(t.role_id) +
                   ", rating=" + std::to_string(t.rating) + ")";
        });

    // ==================== TeamResult ====================
    py::class_<TeamResult>(m, "TeamResult")
        .def(py::init<>())
        .def(py::init([](const std::string& name, const std::vector<TeamPlayerResult>& players) {
            return TeamResult{name, players};
        }), py::arg("name"), py::arg("players"))
        .def_readwrite("name", &TeamResult::name)
        .def_readwrite("players", &TeamResult::players)
        // Backwards compatibility alias
        .def_property("team_id",
            [](const TeamResult& t) { return t.name; },
            [](TeamResult& t, const std::string& v) { t.name = v; },
            "Alias for name (backwards compatibility)")
        .def("__repr__", [](const TeamResult& t) {
            return "TeamResult(name='" + t.name + 
                   "', players=[" + std::to_string(t.players.size()) + " players])";
        });

    // ==================== BalanceResultData ====================
    py::class_<BalanceResultData>(m, "BalanceResultData")
        .def(py::init<>())
        .def_readwrite("quality", &BalanceResultData::quality)
        .def_readwrite("teams", &BalanceResultData::teams)
        .def_readwrite("team_mask", &BalanceResultData::team_mask)
        .def_readwrite("role_mask1", &BalanceResultData::role_mask1)
        .def_readwrite("role_mask2", &BalanceResultData::role_mask2)
        .def("to_dict", [](const BalanceResultData& r) {
            py::dict d;
            d["team_mask"] = r.team_mask;
            d["role_mask1"] = r.role_mask1;
            d["role_mask2"] = r.role_mask2;
            d["fairness"] = r.quality.fairness;
            d["role_fairness"] = r.quality.role_fairness;
            d["role_points"] = r.quality.role_points;
            d["uniformity"] = r.quality.uniformity;
            d["total"] = r.quality.total();
            return d;
        }, "Convert to dictionary format")
        .def("__repr__", [](const BalanceResultData& r) {
            return "BalanceResultData(total=" + std::to_string(r.quality.total()) +
                   ", team_mask='" + r.team_mask + "')";
        });

    // ==================== BalanceResponse ====================
    py::class_<BalanceResponse>(m, "BalanceResponse")
        .def(py::init<>())
        .def_readwrite("result_code", &BalanceResponse::result_code)
        .def_readwrite("status", &BalanceResponse::status)
        .def_readwrite("balances", &BalanceResponse::balances)
        .def_property_readonly("ok", [](const BalanceResponse& r) {
            return r.result_code == 200;
        }, "Check if response is successful")
        .def("__len__", [](const BalanceResponse& r) {
            return r.balances.size();
        })
        .def("__getitem__", [](const BalanceResponse& r, size_t i) {
            if (i >= r.balances.size()) throw py::index_error();
            return r.balances[i];
        })
        .def("__iter__", [](const BalanceResponse& r) {
            return py::make_iterator(r.balances.begin(), r.balances.end());
        }, py::keep_alive<0, 1>())
        .def("__bool__", [](const BalanceResponse& r) {
            return r.result_code == 200 && !r.balances.empty();
        })
        .def("to_dict", [](const BalanceResponse& r) {
            py::dict d;
            d["result"] = r.result_code;
            d["status"] = r.status;
            
            py::list balances_list;
            for (const auto& b : r.balances) {
                py::dict bd;
                bd["team_mask"] = b.team_mask;
                bd["fMask"] = b.role_mask1;
                bd["sMask"] = b.role_mask2;
                bd["dpFairness"] = std::round(b.quality.fairness * 100) / 100;
                bd["rgRolesFairness"] = std::round(b.quality.role_fairness * 100) / 100;
                bd["teamRolePriority"] = std::round(b.quality.role_points * 100) / 100;
                bd["vqUniformity"] = std::round(b.quality.uniformity * 100) / 100;
                bd["result"] = std::round(b.quality.total() * 100) / 100;
                balances_list.append(bd);
            }
            d["active"] = balances_list;
            return d;
        }, "Convert to dictionary format matching Python version output")
        .def("__repr__", [](const BalanceResponse& r) {
            return "BalanceResponse(code=" + std::to_string(r.result_code) +
                   ", status='" + r.status + 
                   "', balances=" + std::to_string(r.balances.size()) + ")";
        });

    // ==================== BalanceEngine ====================
    py::class_<BalanceEngine>(m, "BalanceEngine")
        .def(py::init<const QualitySettings&, 
                      const std::vector<int>&,
                      const std::unordered_map<int, RoleConstraint>&>(),
             py::arg("settings"),
             py::arg("role_ids"),
             py::arg("role_constraints"),
             R"doc(
                Create a new BalanceEngine instance.
                
                Args:
                    settings: QualitySettings for balance calculations
                    role_ids: List of role IDs (e.g., [0, 1, 2] for Tank, DPS, Healer)
                    role_constraints: Dict mapping role_id to RoleConstraint
             )doc")
        .def("find_balances", &BalanceEngine::find_balances,
             py::arg("players"),
             py::arg("team_size"),
             py::arg("balance_limit"),
             py::arg("max_results") = 1000,
             R"doc(
                Find all valid team balances.
                
                Args:
                    players: List of PlayerInfo objects
                    team_size: Number of players per team
                    balance_limit: Maximum allowed balance score
                    max_results: Maximum number of results to return (default: 1000)
                
                Returns:
                    BalanceResponse with sorted balance results
             )doc")
        .def("__repr__", [](const BalanceEngine&) {
            return "BalanceEngine()";
        });

    // ==================== Module-level convenience function ====================
    m.def("find_balances",
        [](const std::vector<PlayerInfo>& players,
           const std::vector<int>& role_ids,
           const std::unordered_map<int, RoleConstraint>& role_constraints,
           int team_size,
           float balance_limit,
           const QualitySettings& settings,
           int max_results) {
            BalanceEngine engine(settings, role_ids, role_constraints);
            return engine.find_balances(players, team_size, balance_limit, max_results);
        },
        py::arg("players"),
        py::arg("role_ids"),
        py::arg("role_constraints"),
        py::arg("team_size"),
        py::arg("balance_limit"),
        py::arg("settings") = QualitySettings{},
        py::arg("max_results") = 1000,
        py::call_guard<py::gil_scoped_release>(),
        R"doc(
            Find team balances (convenience function).
            
            Creates a temporary BalanceEngine and finds balances.
            For repeated calls with same settings, prefer creating 
            a BalanceEngine instance directly.
            
            GIL is released during computation for better concurrency.
        )doc");

    // ==================== Async version for thread pools ====================
    m.def("async_find_balances",
        [](const std::vector<PlayerInfo>& players,
           const std::vector<int>& role_ids,
           const std::unordered_map<int, RoleConstraint>& role_constraints,
           int team_size,
           float balance_limit,
           const QualitySettings& settings,
           int max_results) {
            BalanceEngine engine(settings, role_ids, role_constraints);
            return engine.find_balances(players, team_size, balance_limit, max_results);
        },
        py::arg("players"),
        py::arg("role_ids"),
        py::arg("role_constraints"),
        py::arg("team_size"),
        py::arg("balance_limit"),
        py::arg("settings") = QualitySettings{},
        py::arg("max_results") = 1000,
        py::call_guard<py::gil_scoped_release>(),
        "Alias for find_balances with GIL release (for backwards compatibility)");

    // ==================== Helper factory functions ====================
    m.def("create_player",
        [](int member_id, 
           const std::vector<std::tuple<int, int, int>>& roles) {
            PlayerInfo p;
            p.member_id = member_id;
            for (const auto& [role_id, rating, priority] : roles) {
                p.roles.push_back(RoleRating{role_id, rating, priority});
            }
            return p;
        },
        py::arg("member_id"),
        py::arg("roles"),
        R"doc(
            Create a PlayerInfo from tuple data.
            
            Args:
                member_id: Player's unique ID
                roles: List of (role_id, rating, priority) tuples
            
            Example:
                player = create_player(1, [(0, 2500, 3), (1, 2400, 2)], False)
        )doc");

    m.def("create_settings",
        [](float alpha, float beta, float gamma, 
           float p, float q, float g,
           int max_priority,
           const std::unordered_map<int, float>& role_weights) {
            QualitySettings s;
            s.alpha = alpha;
            s.beta = beta;
            s.gamma = gamma;
            s.p = p;
            s.q = q;
            s.g = g;
            s.max_priority = max_priority;
            s.role_weights = role_weights;
            return s;
        },
        py::arg("alpha") = 1.0f,
        py::arg("beta") = 1.0f,
        py::arg("gamma") = 1.0f,
        py::arg("p") = 1.0f,
        py::arg("q") = 1.0f,
        py::arg("g") = 1.0f,
        py::arg("max_priority") = 3,
        py::arg("role_weights") = std::unordered_map<int, float>{},
        "Create QualitySettings with all parameters");
}