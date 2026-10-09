import json
import csv
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()


def generate_hotel_guests(filename="hotel_guests.csv"):
    """Simulates the legacy Hotel system (Source 1 for SCD Type 2)"""
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["legacy_hotel_id", "first_name", "last_name", "email", "tier", "updated_at"])

        for i in range(1, 101):
            # We add an updated_at timestamp to power our dbt snapshot for SCD Type 2
            writer.writerow(
                [
                    f"HOTEL-{i}",
                    fake.first_name(),
                    fake.last_name(),
                    fake.email(),
                    random.choice(["Silver", "Gold", "VIP", "VVIP"]),
                    datetime.utcnow().isoformat(),
                ]
            )
    print(f"Generated {filename}")


def generate_casino_spins(filename="casino_spins.json", date_str="2026-10-10"):
    """Simulates Casino gaming logs with late-arriving data for incremental logic"""
    spins = []
    base_time = datetime.strptime(date_str, "%Y-%m-%d")

    for i in range(1000):
        # Identity Drift: 20% of players have a new Casino ID, but linkable via email in downstream logic
        is_new_system = random.random() < 0.2
        player_id = f"CASINO-NEW-{random.randint(1, 20)}" if is_new_system else f"HOTEL-{random.randint(1, 100)}"

        # Late-Arriving Data: 5% of spins happened 2 days ago (offline slot machines)
        is_late = random.random() < 0.05
        event_time = (
            base_time - timedelta(days=2) if is_late else base_time - timedelta(minutes=random.randint(1, 1400))
        )

        bet = random.choice([5.0, 10.0, 25.0, 100.0])
        win = bet * random.choice([0, 0, 0, 0, 2, 5])

        spins.append(
            {
                "transaction_id": fake.uuid4(),
                "player_id": player_id,
                "wager_amount": bet,
                "win_amount": win,
                "transaction_ts": event_time.isoformat() + "Z",
            }
        )

    with open(filename, "w") as f:
        for spin in spins:
            f.write(json.dumps(spin) + "\n")
    print(f"Generated {filename}")


if __name__ == "__main__":
    generate_hotel_guests()
    generate_casino_spins()
