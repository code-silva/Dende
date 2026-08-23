# Generated manually to enable PostgreSQL search extensions used by the
# accent-insensitive fuzzy search (HybridSearchView).

from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_remove_branchsupermarket_address_and_more"),
    ]

    operations = [
        TrigramExtension(),
        UnaccentExtension(),
    ]
