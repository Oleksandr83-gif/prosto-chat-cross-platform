from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_number", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255)),
        sa.Column("phone", sa.String(length=32)),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=500)),
        sa.Column("age", sa.Integer),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)
    op.create_index("ix_users_user_number", "users", ["user_number"], unique=True)

    op.create_table(
        "privacy_settings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("show_email", sa.Boolean, nullable=False),
        sa.Column("show_phone", sa.Boolean, nullable=False),
        sa.Column("show_age", sa.Boolean, nullable=False),
        sa.Column("allow_search", sa.Boolean, nullable=False),
    )

    op.create_table(
        "contacts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("owner_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("contact_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("owner_user_id", "contact_user_id", name="uq_owner_contact"),
    )
    op.create_index("ix_contacts_owner_user_id", "contacts", ["owner_user_id"])
    op.create_index("ix_contacts_contact_user_id", "contacts", ["contact_user_id"])

    op.create_table(
        "chats",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=160)),
        sa.Column("owner_user_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_chats_type", "chats", ["type"])
    op.create_index("ix_chats_owner_user_id", "chats", ["owner_user_id"])

    op.create_table(
        "chat_members",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("chat_id", sa.String(length=36), sa.ForeignKey("chats.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_hidden", sa.Boolean, nullable=False),
        sa.Column("joined_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("chat_id", "user_id", name="uq_chat_member"),
    )
    op.create_index("ix_chat_members_chat_id", "chat_members", ["chat_id"])
    op.create_index("ix_chat_members_user_id", "chat_members", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("chat_id", sa.String(length=36), sa.ForeignKey("chats.id"), nullable=False),
        sa.Column("sender_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("body", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("edited_at", sa.DateTime),
        sa.Column("deleted_at", sa.DateTime),
    )
    op.create_index("ix_messages_chat_id", "messages", ["chat_id"])
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    op.create_table(
        "files",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("chat_id", sa.String(length=36), sa.ForeignKey("chats.id"), nullable=False),
        sa.Column("message_id", sa.String(length=36), sa.ForeignKey("messages.id")),
        sa.Column("sender_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120)),
        sa.Column("size_bytes", sa.BigInteger),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_files_chat_id", "files", ["chat_id"])
    op.create_index("ix_files_sender_id", "files", ["sender_id"])


def downgrade() -> None:
    op.drop_index("ix_files_sender_id", table_name="files")
    op.drop_index("ix_files_chat_id", table_name="files")
    op.drop_table("files")
    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_sender_id", table_name="messages")
    op.drop_index("ix_messages_chat_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_chat_members_user_id", table_name="chat_members")
    op.drop_index("ix_chat_members_chat_id", table_name="chat_members")
    op.drop_table("chat_members")
    op.drop_index("ix_chats_owner_user_id", table_name="chats")
    op.drop_index("ix_chats_type", table_name="chats")
    op.drop_table("chats")
    op.drop_index("ix_contacts_contact_user_id", table_name="contacts")
    op.drop_index("ix_contacts_owner_user_id", table_name="contacts")
    op.drop_table("contacts")
    op.drop_table("privacy_settings")
    op.drop_index("ix_users_user_number", table_name="users")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

