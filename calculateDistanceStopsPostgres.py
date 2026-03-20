def GenerateTimes(c, conn, startPoint=None, endPoint=None):
    del conn

    c.execute(
        "ALTER TABLE stopstime ADD COLUMN IF NOT EXISTS distanceRelatedToPreviousStop double precision"
    )
    c.execute(
        "ALTER TABLE stopstime ADD COLUMN IF NOT EXISTS percentageTotalDistance double precision"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_stopstime_trip_sequence ON stopstime (trip_id, stop_sequence)"
    )

    params = {
        "start_point": startPoint,
        "end_point": endPoint,
    }

    c.execute(
        """
        WITH selected_trips AS (
            SELECT trip_id
            FROM (
                SELECT trip_id, ROW_NUMBER() OVER (ORDER BY trip_id) AS trip_position
                FROM trip
            ) ranked
            WHERE (%(start_point)s IS NULL OR trip_position >= %(start_point)s)
              AND (%(end_point)s IS NULL OR trip_position < %(end_point)s)
        ),
        last_stops AS (
            SELECT DISTINCT ON (s.trip_id)
                   s.trip_id,
                   st.stop_name
            FROM stopstime s
            JOIN selected_trips selected ON selected.trip_id = s.trip_id
            JOIN stops st ON st.stop_id = s.stop_id
            ORDER BY s.trip_id, s.stop_sequence DESC
        )
        UPDATE trip t
        SET trip_headsign = last_stops.stop_name
        FROM last_stops
        WHERE t.trip_id = last_stops.trip_id
          AND COALESCE(t.trip_headsign, '') <> COALESCE(last_stops.stop_name, '')
        """,
        params,
    )

    c.execute(
        """
        WITH selected_trips AS (
            SELECT trip_id
            FROM (
                SELECT trip_id, ROW_NUMBER() OVER (ORDER BY trip_id) AS trip_position
                FROM trip
            ) ranked
            WHERE (%(start_point)s IS NULL OR trip_position >= %(start_point)s)
              AND (%(end_point)s IS NULL OR trip_position < %(end_point)s)
        ),
        ordered_stops AS (
            SELECT
                st.trip_id,
                st.stop_id,
                st.stop_sequence,
                st.arrival_time,
                st.departure_time,
                stops.stop_lat::double precision AS stop_lat,
                stops.stop_lon::double precision AS stop_lon,
                LAG(stops.stop_lat::double precision) OVER (
                    PARTITION BY st.trip_id
                    ORDER BY st.stop_sequence
                ) AS prev_stop_lat,
                LAG(stops.stop_lon::double precision) OVER (
                    PARTITION BY st.trip_id
                    ORDER BY st.stop_sequence
                ) AS prev_stop_lon,
                ROW_NUMBER() OVER (
                    PARTITION BY st.trip_id
                    ORDER BY st.stop_sequence
                ) AS stop_rank,
                ROW_NUMBER() OVER (
                    PARTITION BY st.trip_id
                    ORDER BY st.stop_sequence DESC
                ) AS reverse_stop_rank,
                COUNT(*) OVER (PARTITION BY st.trip_id) AS stop_count
            FROM stopstime st
            JOIN selected_trips selected ON selected.trip_id = st.trip_id
            JOIN stops ON stops.stop_id = st.stop_id
        ),
        distances AS (
            SELECT
                ordered_stops.*,
                CASE
                    WHEN prev_stop_lat IS NULL OR prev_stop_lon IS NULL THEN 0.0
                    ELSE 2 * 6373.0 * ASIN(
                        SQRT(
                            POWER(SIN(RADIANS(stop_lat - prev_stop_lat) / 2), 2)
                            + COS(RADIANS(prev_stop_lat))
                            * COS(RADIANS(stop_lat))
                            * POWER(SIN(RADIANS(stop_lon - prev_stop_lon) / 2), 2)
                        )
                    )
                END AS distance_to_previous_stop,
                MAX(
                    CASE
                        WHEN stop_rank = 1 THEN COALESCE(NULLIF(BTRIM(departure_time), ''), NULLIF(BTRIM(arrival_time), ''))
                    END
                ) OVER (PARTITION BY trip_id) AS first_stop_time,
                MAX(
                    CASE
                        WHEN reverse_stop_rank = 1 THEN COALESCE(NULLIF(BTRIM(arrival_time), ''), NULLIF(BTRIM(departure_time), ''))
                    END
                ) OVER (PARTITION BY trip_id) AS last_stop_time,
                MAX(
                    CASE
                        WHEN stop_rank NOT IN (1, stop_count)
                             AND (
                                 NULLIF(BTRIM(arrival_time), '') IS NULL
                                 OR NULLIF(BTRIM(departure_time), '') IS NULL
                             ) THEN 1
                        ELSE 0
                    END
                ) OVER (PARTITION BY trip_id) AS has_missing_intermediate_times
            FROM ordered_stops
        ),
        metrics AS (
            SELECT
                distances.*,
                SUM(distance_to_previous_stop) OVER (PARTITION BY trip_id) AS total_distance,
                SUM(distance_to_previous_stop) OVER (
                    PARTITION BY trip_id
                    ORDER BY stop_sequence
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS cumulative_distance,
                CASE
                    WHEN first_stop_time ~ '^\\d+:\\d{2}:\\d{2}$' THEN
                        split_part(first_stop_time, ':', 1)::integer * 3600
                        + split_part(first_stop_time, ':', 2)::integer * 60
                        + split_part(first_stop_time, ':', 3)::integer
                END AS first_stop_seconds,
                CASE
                    WHEN last_stop_time ~ '^\\d+:\\d{2}:\\d{2}$' THEN
                        split_part(last_stop_time, ':', 1)::integer * 3600
                        + split_part(last_stop_time, ':', 2)::integer * 60
                        + split_part(last_stop_time, ':', 3)::integer
                END AS last_stop_seconds,
                CASE
                    WHEN COALESCE(arrival_time, departure_time) ~ '^\\d+:\\d{2}:\\d{2}$' THEN
                        split_part(COALESCE(arrival_time, departure_time), ':', 1)::integer * 3600
                        + split_part(COALESCE(arrival_time, departure_time), ':', 2)::integer * 60
                        + split_part(COALESCE(arrival_time, departure_time), ':', 3)::integer
                END AS known_time_seconds
            FROM distances
        ),
        interpolated AS (
            SELECT
                metrics.*,
                CASE
                    WHEN stop_count <= 1 THEN 0.0
                    WHEN total_distance > 0 THEN cumulative_distance / total_distance
                    ELSE (stop_rank - 1)::double precision / NULLIF(stop_count - 1, 0)
                END AS progress_ratio,
                CASE
                    WHEN total_distance > 0 THEN distance_to_previous_stop / total_distance
                    WHEN stop_count <= 1 THEN 0.0
                    ELSE 1.0 / NULLIF(stop_count - 1, 0)
                END AS segment_ratio,
                CASE
                    WHEN first_stop_seconds IS NULL OR last_stop_seconds IS NULL THEN NULL
                    WHEN last_stop_seconds >= first_stop_seconds THEN last_stop_seconds - first_stop_seconds
                    ELSE last_stop_seconds + 86400 - first_stop_seconds
                END AS total_duration_seconds
            FROM metrics
        ),
        anchored AS (
            SELECT
                interpolated.*,
                MAX(
                    CASE
                        WHEN known_time_seconds IS NOT NULL THEN stop_sequence
                    END
                ) OVER (
                    PARTITION BY trip_id
                    ORDER BY stop_sequence
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS prev_known_sequence,
                MAX(
                    CASE
                        WHEN known_time_seconds IS NOT NULL THEN cumulative_distance
                    END
                ) OVER (
                    PARTITION BY trip_id
                    ORDER BY stop_sequence
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS prev_known_cumulative_distance,
                MAX(
                    CASE
                        WHEN known_time_seconds IS NOT NULL THEN known_time_seconds
                    END
                ) OVER (
                    PARTITION BY trip_id
                    ORDER BY stop_sequence
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS prev_known_seconds,
                MIN(
                    CASE
                        WHEN known_time_seconds IS NOT NULL THEN stop_sequence
                    END
                ) OVER (
                    PARTITION BY trip_id
                    ORDER BY stop_sequence
                    ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
                ) AS next_known_sequence,
                MIN(
                    CASE
                        WHEN known_time_seconds IS NOT NULL THEN cumulative_distance
                    END
                ) OVER (
                    PARTITION BY trip_id
                    ORDER BY stop_sequence
                    ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
                ) AS next_known_cumulative_distance,
                MIN(
                    CASE
                        WHEN known_time_seconds IS NOT NULL THEN known_time_seconds
                    END
                ) OVER (
                    PARTITION BY trip_id
                    ORDER BY stop_sequence
                    ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
                ) AS next_known_seconds
            FROM interpolated
        ),
        estimated_times AS (
            SELECT
                anchored.*,
                CASE
                    WHEN known_time_seconds IS NOT NULL THEN known_time_seconds
                    WHEN prev_known_seconds IS NOT NULL
                         AND next_known_seconds IS NOT NULL
                         AND next_known_sequence > prev_known_sequence THEN
                        CASE
                            WHEN next_known_cumulative_distance > prev_known_cumulative_distance THEN
                                prev_known_seconds
                                + ROUND(
                                    (
                                        CASE
                                            WHEN next_known_seconds >= prev_known_seconds THEN
                                                next_known_seconds - prev_known_seconds
                                            ELSE
                                                next_known_seconds + 86400 - prev_known_seconds
                                        END
                                    )
                                    * (
                                        (cumulative_distance - prev_known_cumulative_distance)
                                        / NULLIF(
                                            next_known_cumulative_distance - prev_known_cumulative_distance,
                                            0
                                        )
                                    )
                                )::integer
                            ELSE
                                prev_known_seconds
                                + ROUND(
                                    (
                                        CASE
                                            WHEN next_known_seconds >= prev_known_seconds THEN
                                                next_known_seconds - prev_known_seconds
                                            ELSE
                                                next_known_seconds + 86400 - prev_known_seconds
                                        END
                                    )
                                    * (
                                        (stop_rank - prev_known_sequence)::double precision
                                        / NULLIF(next_known_sequence - prev_known_sequence, 0)
                                    )
                                )::integer
                        END
                    WHEN total_duration_seconds IS NULL THEN NULL
                    ELSE first_stop_seconds + ROUND(total_duration_seconds * progress_ratio)::integer
                END AS estimated_time_seconds
            FROM anchored
        ),
        updated_rows AS (
            UPDATE stopstime target
            SET arrival_time = CASE
                    WHEN NULLIF(BTRIM(target.arrival_time), '') IS NULL AND estimated_times.estimated_time_seconds IS NOT NULL THEN
                        LPAD((estimated_times.estimated_time_seconds / 3600)::text, 2, '0')
                        || ':' || LPAD(((estimated_times.estimated_time_seconds %% 3600) / 60)::text, 2, '0')
                        || ':' || LPAD((estimated_times.estimated_time_seconds %% 60)::text, 2, '0')
                    ELSE target.arrival_time
                END,
                departure_time = CASE
                    WHEN NULLIF(BTRIM(target.departure_time), '') IS NULL AND estimated_times.estimated_time_seconds IS NOT NULL THEN
                        LPAD((estimated_times.estimated_time_seconds / 3600)::text, 2, '0')
                        || ':' || LPAD(((estimated_times.estimated_time_seconds %% 3600) / 60)::text, 2, '0')
                        || ':' || LPAD((estimated_times.estimated_time_seconds %% 60)::text, 2, '0')
                    ELSE target.departure_time
                END,
                distanceRelatedToPreviousStop = estimated_times.distance_to_previous_stop,
                percentageTotalDistance = estimated_times.segment_ratio
            FROM estimated_times
            WHERE target.trip_id = estimated_times.trip_id
              AND target.stop_id = estimated_times.stop_id
              AND target.stop_sequence = estimated_times.stop_sequence
              AND estimated_times.has_missing_intermediate_times = 1
              AND estimated_times.first_stop_seconds IS NOT NULL
              AND estimated_times.last_stop_seconds IS NOT NULL
            RETURNING 1
        )
        SELECT COUNT(*)
        FROM updated_rows
        """,
        params,
    )

    updated_rows = c.fetchone()[0]
    print(f"Interpolated stop times for {updated_rows} stop rows")
    return updated_rows
