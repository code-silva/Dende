# Generated manually to enable PostgreSQL search extensions used by the
# accent-insensitive fuzzy search (HybridSearchView).

from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0003_sync_supabase"),
        (
            "app",
            "0003_remove_branchsupermarket_branchsupermarket_coordinates_and_parent_supermarket_uniqueness_and_more",
        ),
    ]

    operations = [
        TrigramExtension(),
        UnaccentExtension(),
    ]
