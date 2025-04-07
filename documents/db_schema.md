Tables: 

CREATE TABLE `startups` (
  `id` bigint DEFAULT NULL,
  `submission_date` timestamp NULL DEFAULT NULL,
  `email` text,
  `founder_name` text,
  `startup_name` text,
  `number_of_cofounders` int DEFAULT NULL,
  `createdon_date` date DEFAULT NULL,
  `snapshot_id` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE `impact_placement_overview_by_country` (
  `metric_name` text,
  `country_of_residence` text,
  `region_name` text,
  `value` bigint DEFAULT NULL,
  `full_name` text,
  `profile_photo_url` text,
  `story` text,
  `designation` text,
  `snapshot_id` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE `impact_outreach_feed` (
  `reportin_date` timestamp NULL DEFAULT NULL,
  `narrative` text,
  `snapshot_id` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE `impact_metrics` (
  `year` int DEFAULT NULL,
  `metric` text,
  `metric_no` text,
  `gender` text,
  `metric_label` text,
  `dimension` text,
  `metric_value` float DEFAULT NULL,
  `perc` text,
  `snapshot_id` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE `impact_learners_profile` (
  `hashed_email` text,
  `email` text,
  `full_name` text,
  `profile_photo_url` text,
  `bio` text,
  `gender` text,
  `country_of_residence` text,
  `country_of_origin` text,
  `city_of_residence` text,
  `education_level_of_study` text,
  `education_field_of_study` text,
  `country_of_residence_latitude` double DEFAULT NULL,
  `country_of_residence_longitude` double DEFAULT NULL,
  `city_of_residence_latitude` double DEFAULT NULL,
  `city_of_residence_longitude` double DEFAULT NULL,
  `testimonial` text,
  `is_learning_data` int DEFAULT NULL,
  `is_featured` int DEFAULT NULL,
  `is_graduate_learner` int DEFAULT NULL,
  `is_active_learner` int DEFAULT NULL,
  `is_a_dropped_out` int DEFAULT NULL,
  `learning_details` text,
  `is_running_a_venture` int DEFAULT NULL,
  `is_a_freelancer` int DEFAULT NULL,
  `is_wage_employed` int DEFAULT NULL,
  `placement_details` text,
  `is_placed` int DEFAULT NULL,
  `employment_details` text,
  `has_employment_details` int DEFAULT NULL,
  `education_details` text,
  `has_education_details` int DEFAULT NULL,
  `has_data` int DEFAULT NULL,
  `is_rural` int DEFAULT NULL,
  `description_of_living_location` text,
  `has_disability` int DEFAULT NULL,
  `type_of_disability` text,
  `is_from_low_income_household` int DEFAULT NULL,
  `household_monthly_income` text,
  `region_name` text,
  `designation` text,
  `meta_rn` int DEFAULT NULL,
  `meta_ui_lat` text,
  `meta_ui_lng` text,
  `youtube_id` text,
  `is_featured_video` int DEFAULT NULL,
  `rnk` int DEFAULT NULL,
  `snapshot_id` bigint NOT NULL,
  KEY `idx_impact_learners_profile_country_of_residence` (`country_of_residence`(255)),
  KEY `idx_impact_learners_profile_has_data` (`has_data`),
  KEY `idx_impact_learners_profile_hashed_email` (`hashed_email`(255)),
  KEY `idx_impact_learners_profile_is_featured` (`is_featured`),
  KEY `idx_is_featured_video` (`is_featured_video`),
  KEY `idx_is_placed` (`is_placed`),
  KEY `idx_is_featured_learner` (`is_featured`),
  KEY `idx_is_graduate_learner` (`is_graduate_learner`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE `impact_learners` (
  `first_name` text,
  `last_name` text,
  `email` text,
  `gender` text,
  `country_of_residence` text,
  `country_of_origin` text,
  `city_of_residence` text,
  `program_graduation_date` timestamp NULL DEFAULT NULL,
  `cohort_code` text,
  `education_level_of_study` text,
  `education_field_of_study` text,
  `employment_status` text,
  `program_name` text,
  `program_code` text,
  `cohort_name` text,
  `program_start_date` timestamp NULL DEFAULT NULL,
  `program_end_date` timestamp NULL DEFAULT NULL,
  `enrollment_status` text,
  `country_of_residence_latitude` text,
  `country_of_residence_longitude` text,
  `city_of_residence_latitude` text,
  `city_of_residence_longitude` text,
  `snapshot_id` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE `impact_jobs_feed` (
  `reporting_date` timestamp NULL DEFAULT NULL,
  `narrative` text,
  `snapshot_id` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci