"""
Schema metadata for BigQuery tables
Contains descriptions and documentation for tables and columns
"""

SCHEMA_DESCRIPTIONS = {
    "channel_dimension": {
        "description": "Distribution channels for content",
        "columns": [
            {
                "name": "channel_uuid",
                "type": "STRING",
                "description": "Unique identifier for each channel"
            },
            {
                "name": "channel",
                "type": "STRING",
                "description": "Name or type of the content distribution channel"
            },
            {
                "name": "insert_datetime",
                "type": "DATETIME",
                "description": "Timestamp when the record was first inserted"
            },
            {
                "name": "update_datetime",
                "type": "DATETIME",
                "description": "Timestamp of the most recent update to the record"
            }
        ]
    },
    "cinema_dimension": {
        "description": "Cinema locations and properties",
        "columns": [
            {
                "name": "cinema_id",
                "type": "INTEGER",
                "description": "Unique ID for the cinema"
            },
            {
                "name": "cinema",
                "type": "STRING",
                "description": "Name of the cinema"
            },
            {
                "name": "cinema_chain",
                "type": "STRING",
                "description": "Chain the cinema belongs to (e.g. Vue, Odeon, AMC)"
            },
            {
                "name": "time_zone",
                "type": "STRING",
                "description": "Time zone in which the cinema operates"
            },
            {
                "name": "cinema_country",
                "type": "STRING",
                "description": "Country where the cinema is located"
            },
            {
                "name": "region",
                "type": "STRING",
                "description": "Administrative region where the cinema is located"
            },
            {
                "name": "city",
                "type": "STRING",
                "description": "City of the cinema"
            },
            {
                "name": "is_europa_cinemas",
                "type": "BOOLEAN",
                "description": "Whether the cinema is part of the Europa Cinemas network"
            },
            {
                "name": "insert_datetime",
                "type": "DATETIME",
                "description": "Record creation timestamp"
            },
            {
                "name": "update_datetime",
                "type": "DATETIME",
                "description": "Last updated timestamp"
            }
        ]
    },
    "content_dimension": {
        "description": "Movies, series and other content",
        "columns": [
            {
                "name": "content_id",
                "type": "INTEGER",
                "description": "Unique ID for each piece of content"
            },
            {
                "name": "title",
                "type": "STRING",
                "description": "Display title of the content"
            },
            {
                "name": "original_title",
                "type": "STRING",
                "description": "Original/native title of the content"
            },
            {
                "name": "content_type",
                "type": "STRING",
                "description": "Type of content (Film, Series, etc.)"
            },
            {
                "name": "release_date",
                "type": "DATE",
                "description": "Official release date"
            },
            {
                "name": "budget",
                "type": "FLOAT",
                "description": "Estimated production budget"
            },
            {
                "name": "revenue",
                "type": "FLOAT",
                "description": "Reported box office or streaming revenue"
            },
            {
                "name": "runtime",
                "type": "INTEGER",
                "description": "Duration in minutes"
            },
            {
                "name": "genres",
                "type": "STRING",
                "description": "Pipe-separated genre labels"
            },
            {
                "name": "production_countries",
                "type": "STRING",
                "description": "Countries where the content was produced"
            },
            {
                "name": "production_companies",
                "type": "STRING",
                "description": "Production companies involved"
            },
            {
                "name": "languages",
                "type": "STRING",
                "description": "Languages used in the content"
            },
            {
                "name": "tags",
                "type": "STRING",
                "description": "Client-defined content tags"
            },
            {
                "name": "imdb_code",
                "type": "STRING",
                "description": "IMDb identifier for the content"
            },
            {
                "name": "insert_datetime",
                "type": "DATETIME",
                "description": "When the content record was created"
            },
            {
                "name": "update_datetime",
                "type": "DATETIME",
                "description": "When the content record was last updated"
            }
        ]
    },
    "content_star_mapping": {
        "description": "Links between content and stars/crew",
        "columns": [
            {
                "name": "content_id",
                "type": "INTEGER",
                "description": "ID of the content the person is linked to"
            },
            {
                "name": "star_id",
                "type": "INTEGER",
                "description": "ID of the actor or crew member"
            },
            {
                "name": "crew_role",
                "type": "STRING",
                "description": "Role or job title (e.g. Actor, Director, Cinematographer)"
            },
            {
                "name": "insert_datetime",
                "type": "DATETIME",
                "description": "Record creation timestamp"
            },
            {
                "name": "update_datetime",
                "type": "DATETIME",
                "description": "Last update timestamp"
            }
        ]
    },
    "showtime_fact": {
        "description": "Cinema screening instances",
        "columns": [
            {
                "name": "content_id",
                "type": "INTEGER",
                "description": "ID of the content being shown"
            },
            {
                "name": "showtime_id",
                "type": "INTEGER",
                "description": "Unique ID for each showtime"
            },
            {
                "name": "cinema_id",
                "type": "INTEGER",
                "description": "Cinema where the showtime occurs"
            },
            {
                "name": "local_show_datetime",
                "type": "DATETIME",
                "description": "Showtime in cinema's local time zone"
            },
            {
                "name": "utc_show_datetime",
                "type": "DATETIME",
                "description": "Same showtime converted to UTC"
            },
            {
                "name": "attributes",
                "type": "STRING",
                "description": "Extra info (3D, IMAX, Autism Friendly, etc.)"
            },
            {
                "name": "insert_datetime",
                "type": "DATETIME",
                "description": "When this record was first inserted"
            },
            {
                "name": "update_datetime",
                "type": "DATETIME",
                "description": "When this record was last updated"
            }
        ]
    },
    "star_dimension": {
        "description": "Actors and crew members",
        "columns": [
            {
                "name": "star_id",
                "type": "INTEGER",
                "description": "Unique identifier for the individual"
            },
            {
                "name": "star_name",
                "type": "STRING",
                "description": "Full name of the actor or crew member"
            },
            {
                "name": "gender",
                "type": "STRING",
                "description": "Gender of the individual (if available)"
            },
            {
                "name": "insert_datetime",
                "type": "DATETIME",
                "description": "When the star record was created"
            },
            {
                "name": "update_datetime",
                "type": "DATETIME",
                "description": "Last updated timestamp for the record"
            }
        ]
    },
    "streaming_run": {
        "description": "Aggregated streaming availability",
        "columns": [
            {
                "name": "content_id",
                "type": "INTEGER",
                "description": "ID of the content available online"
            },
            {
                "name": "title",
                "type": "STRING",
                "description": "Title of the content"
            },
            {
                "name": "streaming_country",
                "type": "STRING",
                "description": "Country in which it is/was streaming"
            },
            {
                "name": "platform",
                "type": "STRING",
                "description": "Platform name (Netflix, Amazon, etc.)"
            },
            {
                "name": "streaming_type",
                "type": "STRING",
                "description": "Streaming model (SVOD, AVOD, TVOD, etc.)"
            },
            {
                "name": "streaming_format",
                "type": "STRING",
                "description": "Format (e.g. SD, HD, 4K) — may be 'Unknown'"
            },
            {
                "name": "total_streamings",
                "type": "INTEGER",
                "description": "Number of distinct streaming links or records aggregated"
            },
            {
                "name": "streaming_run_weeks",
                "type": "INTEGER",
                "description": "Number of weeks the content has been available online"
            }
        ]
    },
    "streamings_fact": {
        "description": "Individual streaming instances",
        "columns": [
            {
                "name": "content_id",
                "type": "INTEGER",
                "description": "ID of the streamed content"
            },
            {
                "name": "streaming_id",
                "type": "INTEGER",
                "description": "Unique ID for the specific streaming instance"
            },
            {
                "name": "platform",
                "type": "STRING",
                "description": "Platform offering the content (e.g. Hulu, Netflix)"
            },
            {
                "name": "streaming_country",
                "type": "STRING",
                "description": "Country where the platform made it available"
            },
            {
                "name": "streaming_type",
                "type": "STRING",
                "description": "Streaming type (SVOD, TVOD, AVOD, TV)"
            },
            {
                "name": "tvod_purchase_type",
                "type": "STRING",
                "description": "If TVOD, whether it's a purchase or rental"
            },
            {
                "name": "streaming_format",
                "type": "STRING",
                "description": "Video format or quality level"
            },
            {
                "name": "price",
                "type": "NUMERIC",
                "description": "Cost to the consumer (for TVOD)"
            },
            {
                "name": "currency_badge",
                "type": "STRING",
                "description": "Symbol of the currency (e.g. $, €, £)"
            },
            {
                "name": "currency_iso",
                "type": "STRING",
                "description": "ISO currency code (e.g. USD, EUR, GBP)"
            },
            {
                "name": "stream_created_datetime",
                "type": "DATETIME",
                "description": "When the stream became active"
            },
            {
                "name": "stream_disabled_datetime",
                "type": "DATETIME",
                "description": "When it was disabled (if applicable)"
            },
            {
                "name": "insert_datetime",
                "type": "DATETIME",
                "description": "Timestamp of insertion"
            },
            {
                "name": "update_datetime",
                "type": "DATETIME",
                "description": "Last modified timestamp"
            }
        ]
    },
    "theatrical_run": {
        "description": "Weekly theatrical performance metrics",
        "columns": [
            {
                "name": "content_id",
                "type": "INTEGER",
                "description": "ID of the film being tracked for theatrical release"
            },
            {
                "name": "title",
                "type": "STRING",
                "description": "Title of the film"
            },
            {
                "name": "cinema_country",
                "type": "STRING",
                "description": "Country of the theatrical release"
            },
            {
                "name": "release_date",
                "type": "DATE",
                "description": "Film's original release date"
            },
            {
                "name": "week_start",
                "type": "DATE",
                "description": "Start of the tracked week"
            },
            {
                "name": "showtimes",
                "type": "INTEGER",
                "description": "Number of showings in that week"
            },
            {
                "name": "showtime_ratio",
                "type": "FLOAT",
                "description": "Ratio of weekly showtimes compared to first week (percentage)"
            },
            {
                "name": "flag",
                "type": "INTEGER",
                "description": "1 if showtime_ratio > 30% (indicates strong hold), otherwise 0"
            }
        ]
    },
    "temp1": {
        "description": "Temporary table for cinema showtime aggregations",
        "columns": [
            {
                "name": "title",
                "type": "STRING",
                "description": "Title of the content"
            },
            {
                "name": "cinema",
                "type": "STRING",
                "description": "Name of the cinema"
            },
            {
                "name": "cinema_country",
                "type": "STRING",
                "description": "Country where the cinema is located"
            },
            {
                "name": "shows",
                "type": "INTEGER",
                "description": "Number of shows/screenings"
            }
        ]
    },
    "temp2": {
        "description": "Temporary table for streaming aggregations",
        "columns": [
            {
                "name": "title",
                "type": "STRING",
                "description": "Title of the content"
            },
            {
                "name": "platform",
                "type": "STRING",
                "description": "Streaming platform name"
            },
            {
                "name": "streaming_country",
                "type": "STRING",
                "description": "Country where content is streamed"
            },
            {
                "name": "links",
                "type": "INTEGER",
                "description": "Number of streaming links/instances"
            }
        ]
    }
} 