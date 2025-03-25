import json
import os
from datetime import datetime, timezone

class IGN:
    def __init__(self, username: str):
        self.username = username

    def __str__(self):
        return self.username

    def to_dict(self):
        return {"username": self.username}

    @classmethod
    def from_dict(cls, data: dict) -> "IGN":
        return cls(username=data.get("username", ""))


class Ticket:
    def __init__(
        self,
        ticket_id: str,
        user_id: str,
        channel_id: str,
        subject: str = "",
        reason: str = "",
        category: str = "General Support",
        ign: IGN = None,
        status: str = "open",
        created_at: str = None,
        updated_at: str = None,
        logs: list = None,
    ):
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.channel_id = channel_id
        self.subject = subject
        self.reason = reason
        self.category = category
        self.ign = ign
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or datetime.now(timezone.utc).isoformat()
        self.logs = logs if logs is not None else []

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "subject": self.subject,
            "reason": self.reason,
            "category": self.category,
            "ign": self.ign.to_dict() if self.ign else None,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "logs": self.logs,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ticket":
        ign_data = data.get("ign")
        ign = IGN.from_dict(ign_data) if ign_data else None
        return cls(
            ticket_id=data.get("ticket_id"),
            user_id=data.get("user_id"),
            channel_id=data.get("channel_id"),
            subject=data.get("subject", ""),
            reason=data.get("reason", ""),
            category=data.get("category", "General Support"),
            ign=ign,
            status=data.get("status", "open"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            logs=data.get("logs", []),
        )

    def add_log(self, message: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        self.logs.append({"timestamp": timestamp, "message": message})
        self.updated_at = timestamp


class TicketHandler:
    def __init__(self, storage_file="data/tickets.json"):
        self.storage_file = storage_file
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        try:
            with open(self.storage_file, "r") as f:
                tickets_data = json.load(f)
                self.tickets = {
                    ticket_id: Ticket.from_dict(ticket_dict)
                    for ticket_id, ticket_dict in tickets_data.items()
                }
        except FileNotFoundError:
            self.tickets = {}

    def save(self):
        with open(self.storage_file, "w") as f:
            json.dump(
                {ticket_id: ticket.to_dict() for ticket_id, ticket in self.tickets.items()},
                f,
                indent=4,
            )

    def _generate_ticket_id(self) -> str:
        if self.tickets:
            max_id = max(int(ticket_id) for ticket_id in self.tickets.keys())
            next_id = max_id + 1
        else:
            next_id = 1

        if next_id < 1000:
            return str(next_id).zfill(3)
        else:
            return str(next_id).zfill(4)

    def create_ticket(self, user_id: str, channel_id: str, subject: str, reason: str, ign_username: str,
                      category: str = "General Support") -> Ticket:
        ticket_id = self._generate_ticket_id()
        ign = IGN(ign_username)
        new_ticket = Ticket(
            ticket_id=ticket_id,
            user_id=user_id,
            channel_id=channel_id,
            subject=subject,
            reason=reason,
            category=category,
            ign=ign,
        )
        self.tickets[new_ticket.ticket_id] = new_ticket
        self.save()
        return new_ticket

    def delete_ticket(self, ticket_id: str):
        if ticket_id in self.tickets:
            del self.tickets[ticket_id]
            self.save()

    def update_ticket(self, ticket_id: str, **kwargs) -> Ticket:
        ticket = self.tickets.get(ticket_id)
        if ticket:
            for key, value in kwargs.items():
                if key == "ign" and isinstance(value, str):
                    setattr(ticket, key, IGN(value))
                elif hasattr(ticket, key):
                    setattr(ticket, key, value)
            ticket.updated_at = datetime.now(timezone.utc).isoformat()
            self.save()
        return ticket

    def add_ticket_log(self, ticket_id: str, message: str) -> Ticket:
        ticket = self.tickets.get(ticket_id)
        if ticket:
            ticket.add_log(message)
            self.save()
        return ticket

    def add_ticket_log_with_user(self, ticket_id: str, user_id: str, display_name: str, message: str) -> Ticket:
        log_message = f"[{display_name} ({user_id})]: {message}"
        return self.add_ticket_log(ticket_id, log_message)

    def close_ticket(self, ticket_id: str, closing_message: str = None) -> Ticket:
        ticket = self.tickets.get(ticket_id)
        if ticket:
            ticket.status = "closed"
            if closing_message:
                ticket.add_log(f"Ticket closed: {closing_message}")
            else:
                ticket.add_log("Ticket closed.")
            self.save()
        return ticket

    def get_ticket(self, ticket_id: str) -> Ticket:
        return self.tickets.get(ticket_id)

    def list_tickets(self) -> list:
        return list(self.tickets.values())

    # NEW: Helper method to check if a user already has an open ticket.
    def has_open_ticket(self, user_id: str) -> bool:
        return any(ticket.user_id == user_id and ticket.status == "open" for ticket in self.tickets.values())


# Example usage:
if __name__ == "__main__":
    handler = TicketHandler("data/tickets.json")

    # Create a new ticket with category "Bug Report"
    new_ticket = handler.create_ticket(
        user_id="123456789",
        channel_id="987654321",
        subject="Server Connection Issue",
        reason="I am unable to join the server.",
        ign_username="MyMinecraftIGN",
        category="Bug Report"
    )
    print("New ticket created:", new_ticket.to_dict())

    # Add a log entry to the ticket using add_ticket_log_with_user.
    handler.add_ticket_log_with_user(new_ticket.ticket_id, "123456789", "ExampleUser", "Initial troubleshooting started.")

    # Close the ticket with a closing message.
    handler.close_ticket(new_ticket.ticket_id, "Issue resolved.")

    # List all tickets.
    for ticket in handler.list_tickets():
        print(ticket.to_dict())
