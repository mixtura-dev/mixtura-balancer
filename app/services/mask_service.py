import itertools
from uuid import UUID

from app.models.player import Player
from app.models.settings import BalanceSettings


class MaskService:
    """Сервис для генерации и проверки масок распределения"""

    @staticmethod
    def generate_team_masks(total_players: int, team_size: int) -> list[tuple[int, ...]]:
        """
        Генерация масок распределения игроков по командам.
        0 = первая команда, 1 = вторая команда
        """
        masks = []

        for combination in itertools.combinations(range(total_players), team_size):
            mask = [1] * total_players
            for idx in combination:
                mask[idx] = 0
            masks.append(tuple(mask))

        return masks

    @staticmethod
    def generate_role_masks(
        team_size: int,
        role_constraints: dict[UUID, tuple[int, int]],  # role_id -> (min, max)
    ) -> tuple[list[UUID], list[tuple[int, ...]]]:
        """
        Генерация масок распределения ролей в команде (по индексам).
        Возвращает (список UUID ролей, список масок с индексами).
        """
        role_ids = list(role_constraints.keys())
        role_id_to_idx = {role_id: idx for idx, role_id in enumerate(role_ids)}

        def generate_combinations(
            remaining_slots: int,
            current_counts: dict[int, int],
            current_assignment: tuple[int, ...],
        ) -> list[tuple[int, ...]]:
            if remaining_slots == 0:
                # Проверяем минимальные требования
                for role_id, (min_count, _) in role_constraints.items():
                    idx = role_id_to_idx[role_id]
                    if current_counts.get(idx, 0) < min_count:
                        return []
                return [current_assignment]

            results = []
            for role_id, idx in role_id_to_idx.items():
                _, max_count = role_constraints[role_id]
                current_count = current_counts.get(idx, 0)

                if current_count < max_count:
                    new_counts = current_counts.copy()
                    new_counts[idx] = current_count + 1
                    new_assignment = current_assignment + (idx,)

                    results.extend(
                        generate_combinations(remaining_slots - 1, new_counts, new_assignment)
                    )

            return results

        masks = generate_combinations(team_size, {}, ())
        return role_ids, masks

    @staticmethod
    def validate_role_assignment(
        players: list[Player], role_mask: tuple[int, ...], role_ids: list[UUID]
    ) -> bool:
        """Проверка, могут ли игроки играть назначенные роли"""
        if len(players) != len(role_mask):
            return False

        for player, role_idx in zip(players, role_mask):
            role_id = role_ids[role_idx]
            if not player.can_play_role(role_id):
                return False

        return True

    def get_valid_role_masks(
        self, players: list[Player], settings: BalanceSettings
    ) -> tuple[list[UUID], list[tuple[tuple[int, ...], tuple[int, ...]]]]:
        """Получение всех валидных масок ролей для списка игроков"""
        role_constraints = {
            role_id: (rs.min_in_team, rs.max_in_team) for role_id, rs in settings.roles.items()
        }

        role_ids, all_masks = self.generate_role_masks(len(players), role_constraints)

        valid_masks = []
        for mask in all_masks:
            # Проверяем все перестановки игроков
            for perm in itertools.permutations(range(len(players))):
                permuted_players = [players[i] for i in perm]
                if self.validate_role_assignment(permuted_players, mask, role_ids):
                    # Сохраняем маску с индексами
                    valid_masks.append((perm, mask))
                    break  # Достаточно одной валидной перестановки

        return role_ids, valid_masks
