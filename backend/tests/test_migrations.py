import os

import alembic.command
import alembic.config


def test_alembic_upgrade_and_downgrade():
    """Verify that Alembic migrations apply and roll back cleanly (Task P2.1, P2.3)."""
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ini_path = os.path.join(backend_dir, "alembic.ini")
    migrations_dir = os.path.join(backend_dir, "migrations")

    config = alembic.config.Config(ini_path)
    config.set_main_option("script_location", migrations_dir)

    # Downgrade to base (clean state)
    alembic.command.downgrade(config, "base")

    # Upgrade to head
    alembic.command.upgrade(config, "head")

    # Re-downgrade to base
    alembic.command.downgrade(config, "base")

    # Re-upgrade to head so database remains in ready state
    alembic.command.upgrade(config, "head")
