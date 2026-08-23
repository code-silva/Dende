# Generated manually to add GIN trigram indexes for the Product fuzzy search
# fields, avoiding Sequential Scan on TrigramSimilarity/Unaccent queries.

import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0004_enable_search_extensions"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="product",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["name"],
                name="product_name_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["brand"],
                name="product_brand_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
