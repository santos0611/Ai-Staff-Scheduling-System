-- Clean local database schema for the AI Staff Scheduling System
-- Table definitions only: no personal/test data or credentials.

CREATE DATABASE IF NOT EXISTS staff_rota
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE staff_rota;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `staff`;
CREATE TABLE `staff` (
  `staff_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `dob` date DEFAULT NULL,
  `position` varchar(50) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `account_status` varchar(20) DEFAULT 'Approved',
  `is_admin` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`staff_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `shifts`;
CREATE TABLE `shifts` (
  `shift_id` int NOT NULL AUTO_INCREMENT,
  `shift_date` date DEFAULT NULL,
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL,
  `required_role` varchar(50) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'Draft',
  `is_open_shift` tinyint(1) DEFAULT '0',
  `notes` varchar(255) DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`shift_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `availability`;
CREATE TABLE `availability` (
  `availability_id` int NOT NULL AUTO_INCREMENT,
  `staff_id` int NOT NULL,
  `day_of_week` varchar(20) NOT NULL,
  `is_available` tinyint(1) DEFAULT '1',
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL,
  `is_all_day` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`availability_id`),
  KEY `staff_id` (`staff_id`),
  CONSTRAINT `availability_ibfk_1` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `drop_requests`;
CREATE TABLE `drop_requests` (
  `drop_request_id` int NOT NULL AUTO_INCREMENT,
  `shift_id` int NOT NULL,
  `staff_id` int NOT NULL,
  `status` varchar(20) DEFAULT 'Pending',
  `requested_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`drop_request_id`),
  KEY `shift_id` (`shift_id`),
  KEY `staff_id` (`staff_id`),
  CONSTRAINT `drop_requests_ibfk_1` FOREIGN KEY (`shift_id`) REFERENCES `shifts` (`shift_id`),
  CONSTRAINT `drop_requests_ibfk_2` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `manager_cleared_notifications`;
CREATE TABLE `manager_cleared_notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `manager_staff_id` int NOT NULL,
  `shift_id` int NOT NULL,
  `cleared_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_manager_shift` (`manager_staff_id`,`shift_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `shift_pickups`;
CREATE TABLE `shift_pickups` (
  `pickup_id` int NOT NULL AUTO_INCREMENT,
  `shift_id` int NOT NULL,
  `staff_id` int NOT NULL,
  `status` varchar(20) DEFAULT 'Pending',
  `requested_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `staff_cleared` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`pickup_id`),
  KEY `shift_id` (`shift_id`),
  KEY `staff_id` (`staff_id`),
  CONSTRAINT `shift_pickups_ibfk_1` FOREIGN KEY (`shift_id`) REFERENCES `shifts` (`shift_id`),
  CONSTRAINT `shift_pickups_ibfk_2` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `staff_shifts`;
CREATE TABLE `staff_shifts` (
  `staff_shift_id` int NOT NULL AUTO_INCREMENT,
  `staff_id` int DEFAULT NULL,
  `shift_id` int DEFAULT NULL,
  `attendance_status` varchar(50) DEFAULT 'Scheduled',
  PRIMARY KEY (`staff_shift_id`),
  KEY `staff_id` (`staff_id`),
  KEY `shift_id` (`shift_id`),
  CONSTRAINT `staff_shifts_ibfk_1` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`),
  CONSTRAINT `staff_shifts_ibfk_2` FOREIGN KEY (`shift_id`) REFERENCES `shifts` (`shift_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `swap_requests`;
CREATE TABLE `swap_requests` (
  `request_id` int NOT NULL AUTO_INCREMENT,
  `from_staff_id` int DEFAULT NULL,
  `to_staff_id` int DEFAULT NULL,
  `shift_id` int DEFAULT NULL,
  `status` varchar(20) DEFAULT 'Pending',
  PRIMARY KEY (`request_id`),
  KEY `from_staff_id` (`from_staff_id`),
  KEY `to_staff_id` (`to_staff_id`),
  KEY `shift_id` (`shift_id`),
  CONSTRAINT `swap_requests_ibfk_1` FOREIGN KEY (`from_staff_id`) REFERENCES `staff` (`staff_id`),
  CONSTRAINT `swap_requests_ibfk_2` FOREIGN KEY (`to_staff_id`) REFERENCES `staff` (`staff_id`),
  CONSTRAINT `swap_requests_ibfk_3` FOREIGN KEY (`shift_id`) REFERENCES `shifts` (`shift_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `time_off`;
CREATE TABLE `time_off` (
  `time_off_id` int NOT NULL AUTO_INCREMENT,
  `staff_id` int NOT NULL,
  `request_type` varchar(50) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `reason` text,
  `status` varchar(20) DEFAULT 'Pending',
  `manager_note` text,
  `requested_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `reviewed_at` timestamp NULL DEFAULT NULL,
  `staff_cleared` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`time_off_id`),
  KEY `staff_id` (`staff_id`),
  CONSTRAINT `time_off_ibfk_1` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
