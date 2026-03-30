# Quality Metrics Mathematical Description

Balance list is sorted by analyzing each balance using the mathematical formulas described below (hereinafter simply `evaluation`).

## Definitions

Let:
- **X** — list of players in team A
- **Y** — list of players in team B
- **Z** — list of players for both teams A and B
- **sr_x** — skill rating of player x
- **p** — power coefficient for fairness (default: 2.0)
- **q** — power coefficient for uniformity (default: 2.0)

## 1. Fairness (dpFairness)

Measures the difference in total team ratings using p-norm.

### Formula

$$s_p(X) = \left( \sum_{x\in X} sr_x^p \right)^{1/p}$$

$$dpFairness(X, Y) = \alpha \times \left|\left( \sum_{x\in X} sr_x^p \right)^{1/p} - \left( \sum_{y\in Y} sr_y^p \right)^{1/p}\right|$$

Where $\alpha$ is the fairness weight coefficient (default: 3.0).

### Explanation

The formula calculates the p-norm of team ratings, then computes the absolute difference. When $p = 2$, this becomes equivalent to RMS (root mean square). Lower values indicate more equal team strength.

## 2. Role Fairness (dpRoleFairness)

Measures the difference in role-specific ratings between teams.

### Formula

$$r_p(Role) = \left(\left|\sum_{Role_x \in X} sr_{Role_x} - \sum_{Role_y \in Y} sr_{Role_y}\right| \times roleWeight\right)^p$$

$$dpRoleFairness(X, Y) = \beta \times \left( \frac{r_p(Role_1) + r_p(Role_2) + \dots + r_p(Role_n)}{n} \right)^{1/p}$$

Where:
- $\beta$ is the role fairness weight coefficient (default: 1.0)
- $roleWeight$ is the custom weight for each role (default: 1.0)
- $n$ is the number of roles

### Explanation

Role fairness ensures that each role in both teams has similar total rating. The metric accounts for custom role weights (e.g., some roles may be more impactful).

## 3. Uniformity (vqUniformity)

Measures how evenly ratings are distributed within each team.

### Formula

$$MU_z = \frac{\sum_{z\in Z} sr_z}{|Z|}$$

$$vqUniformity(X, Y) = \left| \left( \frac{\sum_{x\in X} |x - MU_z|^q}{|X|} \right)^{1/q} - \left( \frac{\sum_{y\in Y} |y - MU_z|^q}{|Y|} \right)^{1/q} \right|$$

### Explanation

Uniformity penalizes solutions where one team has very high-rated players and low-rated players, while the other team has balanced ratings. Ideally, both teams should have similar internal rating distribution.

## 4. Role Priority Points (RolePriorityPoints)

Measures how well players are assigned to their preferred roles.

### Formula

For each player assigned to a role:

$$\text{lost\_points} = \sum \text{player.priority}$$

$$Imbalance = |T_1 - T_2|$$

$$\text{RolePriorityPoints} = \gamma \times \begin{cases} 
\text{lost\_points} & \text{if } Imbalance \le \text{threshold} \\
\text{lost\_points} + \xi \times Imbalance & \text{if } Imbalance > \text{threshold} 
\end{cases}$$

Where:
- $\gamma$ is the role priority weight coefficient (default: 80.0)
- $\xi$ is the imbalance penalty coefficient (default: 0.2)
- $\text{threshold}$ is the imbalance threshold (default: 1)
- $\text{player.priority}$ — player's priority for the assigned role (lower = better, 1 = main role)

### Explanation

This metric rewards assigning players to their preferred roles. A player with priority=1 (highest) playing their main role loses fewer points than a player with priority=3 playing an off-role.

Additionally, if one team gets significantly more "priority points" than the other, a penalty is applied.

## Total Evaluation

$$Evaluation = \alpha \times dpFairness(X, Y) + \beta \times dpRoleFairness(X, Y) + \gamma \times RolePriorityPoints + vqUniformity(X, Y)$$

Or equivalently:

$$Fairness = \alpha \times dpFairness(X, Y) + \beta \times dpRoleFairness(X, Y)$$

$$Evaluation = Fairness + RolePriorityPoints + vqUniformity$$

Balance results are sorted by **Evaluation** (lower is better).

## Coefficient Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fairness_coef` ($\alpha$) | 3.0 | Weight for fairness |
| `role_fairness_coef` ($\beta$) | 1.0 | Weight for role fairness |
| `role_priority_coef` ($\gamma$) | 80.0 | Weight for role priority |
| `role_priority_imbalance_coef` ($\xi$) | 0.2 | Penalty for priority imbalance |
| `fairness_power_coef` ($p$) | 2.0 | Power for fairness calculation |
| `uniformity_power_coef` ($q$) | 2.0 | Power for uniformity calculation |
| `roleWeight` | 1.0 | Custom weight per role |

## Optimization Algorithm

The engine uses:

1. **Gosper's Hack**: Efficient generation of team split combinations using bitmasks
2. **Parallel Processing**: Multi-threaded evaluation of combinations
3. **Early Pruning**: Skip combinations that exceed quality thresholds
4. **Top-K Heap**: Maintain only the best N results using a priority queue

This allows searching through thousands of possible combinations efficiently.
