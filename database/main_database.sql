-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 13, 2026 at 02:06 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `main_database`
--

-- --------------------------------------------------------

--
-- Table structure for table `activity_logs`
--

CREATE TABLE `activity_logs` (
  `log_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `action` varchar(45) NOT NULL,
  `timestamp` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `data_fields`
--

CREATE TABLE `data_fields` (
  `field_id` int(11) NOT NULL,
  `field_name` varchar(100) NOT NULL,
  `data_type` varchar(45) NOT NULL DEFAULT 'text'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `data_fields`
--

INSERT INTO `data_fields` (`field_id`, `field_name`, `data_type`) VALUES
(1, 'registry_no', 'text'),
(2, 'province', 'text'),
(3, 'city_municipality', 'text'),
(4, 'child_first', 'text'),
(5, 'child_middle', 'text'),
(6, 'child_last', 'text'),
(7, 'sex', 'text'),
(8, 'dob_day', 'text'),
(9, 'dob_month', 'text'),
(10, 'dob_year', 'text'),
(11, 'pob_hospital', 'text'),
(12, 'pob_city', 'text'),
(13, 'pob_province', 'text'),
(14, 'type_of_birth', 'text'),
(15, 'birth_order', 'text'),
(16, 'birth_order_total', 'text'),
(17, 'weight', 'text'),
(18, 'mother_first', 'text'),
(19, 'mother_middle', 'text'),
(20, 'mother_last', 'text'),
(21, 'mother_citizenship', 'text'),
(22, 'mother_religion', 'text'),
(23, 'mother_age', 'text'),
(24, 'mother_address', 'text'),
(25, 'mother_city', 'text'),
(26, 'mother_province', 'text'),
(27, 'mother_children_alive', 'text'),
(28, 'mother_children_living', 'text'),
(29, 'father_first', 'text'),
(30, 'father_middle', 'text'),
(31, 'father_last', 'text'),
(32, 'father_citizenship', 'text'),
(33, 'father_religion', 'text'),
(34, 'father_age', 'text'),
(35, 'father_address', 'text'),
(36, 'father_city', 'text'),
(37, 'father_province', 'text'),
(38, 'father_occupation', 'text'),
(39, 'parents_marriage_month', 'text'),
(40, 'parents_marriage_day', 'text'),
(41, 'parents_marriage_year', 'text'),
(42, 'parents_marriage_city', 'text'),
(43, 'parents_marriage_province', 'text'),
(44, 'parents_marriage_country', 'text'),
(45, 'date_submitted', 'text'),
(46, 'prepared_by', 'text'),
(47, 'deceased_first', 'text'),
(48, 'deceased_middle', 'text'),
(49, 'deceased_last', 'text'),
(50, 'religion', 'text'),
(51, 'age_years', 'text'),
(52, 'age_months', 'text'),
(53, 'age_days', 'text'),
(54, 'pod_hospital', 'text'),
(55, 'pod_city', 'text'),
(56, 'pod_province', 'text'),
(57, 'dod_day', 'text'),
(58, 'dod_month', 'text'),
(59, 'dod_year', 'text'),
(60, 'citizenship', 'text'),
(61, 'residence_address', 'text'),
(62, 'residence_city', 'text'),
(63, 'residence_province', 'text'),
(64, 'civil_status', 'text'),
(65, 'occupation', 'text'),
(66, 'cause_immediate', 'text'),
(67, 'cause_antecedent', 'text'),
(68, 'cause_underlying', 'text'),
(69, 'cause_other', 'text'),
(70, 'corpse_disposal', 'text'),
(71, 'burial_permit_no', 'text'),
(72, 'burial_permit_date', 'text'),
(73, 'autopsy', 'text'),
(74, 'cemetery_address', 'text'),
(75, 'informant_name', 'text'),
(76, 'informant_relationship', 'text'),
(77, 'informant_address', 'text'),
(78, 'informant_date', 'text'),
(79, 'date_received', 'text'),
(80, 'husband_first', 'text'),
(81, 'husband_middle', 'text'),
(82, 'husband_last', 'text'),
(83, 'husband_dob_day', 'text'),
(84, 'husband_dob_month', 'text'),
(85, 'husband_dob_year', 'text'),
(86, 'husband_age', 'text'),
(87, 'husband_pob_city', 'text'),
(88, 'husband_pob_province', 'text'),
(89, 'husband_sex', 'text'),
(90, 'husband_citizenship', 'text'),
(91, 'husband_residence', 'text'),
(92, 'husband_religion', 'text'),
(93, 'husband_civil_status', 'text'),
(94, 'husband_father_first', 'text'),
(95, 'husband_father_last', 'text'),
(96, 'husband_father_citizenship', 'text'),
(97, 'husband_mother_first', 'text'),
(98, 'husband_mother_last', 'text'),
(99, 'husband_mother_citizenship', 'text'),
(100, 'husband_consent_first', 'text'),
(101, 'husband_consent_relationship', 'text'),
(102, 'husband_consent_residence', 'text'),
(103, 'wife_first', 'text'),
(104, 'wife_middle', 'text'),
(105, 'wife_last', 'text'),
(106, 'wife_dob_day', 'text'),
(107, 'wife_dob_month', 'text'),
(108, 'wife_dob_year', 'text'),
(109, 'wife_age', 'text'),
(110, 'wife_pob_city', 'text'),
(111, 'wife_pob_province', 'text'),
(112, 'wife_sex', 'text'),
(113, 'wife_citizenship', 'text'),
(114, 'wife_residence', 'text'),
(115, 'wife_religion', 'text'),
(116, 'wife_civil_status', 'text'),
(117, 'wife_father_first', 'text'),
(118, 'wife_father_last', 'text'),
(119, 'wife_father_citizenship', 'text'),
(120, 'wife_mother_first', 'text'),
(121, 'wife_mother_last', 'text'),
(122, 'wife_mother_citizenship', 'text'),
(123, 'wife_consent_first', 'text'),
(124, 'wife_consent_relationship', 'text'),
(125, 'wife_consent_residence', 'text'),
(126, 'marriage_venue', 'text'),
(127, 'marriage_city', 'text'),
(128, 'marriage_province', 'text'),
(129, 'marriage_day', 'text'),
(130, 'marriage_month', 'text'),
(131, 'marriage_year', 'text'),
(132, 'marriage_time', 'text'),
(133, 'license_no', 'text'),
(134, 'license_date_issued', 'text'),
(135, 'license_place_issued', 'text'),
(136, 'received_by', 'text'),
(137, 'groom_first', 'text'),
(138, 'groom_middle', 'text'),
(139, 'groom_last', 'text'),
(140, 'groom_dob_day', 'text'),
(141, 'groom_dob_month', 'text'),
(142, 'groom_dob_year', 'text'),
(143, 'groom_age', 'text'),
(144, 'groom_pob_city', 'text'),
(145, 'groom_pob_province', 'text'),
(146, 'groom_sex', 'text'),
(147, 'groom_citizenship', 'text'),
(148, 'groom_residence', 'text'),
(149, 'groom_religion', 'text'),
(150, 'groom_civil_status', 'text'),
(151, 'groom_prev_marriage', 'text'),
(152, 'groom_relationship_degree', 'text'),
(153, 'groom_father_first', 'text'),
(154, 'groom_father_middle', 'text'),
(155, 'groom_father_last', 'text'),
(156, 'groom_father_citizenship', 'text'),
(157, 'groom_father_residence', 'text'),
(158, 'groom_mother_first', 'text'),
(159, 'groom_mother_middle', 'text'),
(160, 'groom_mother_last', 'text'),
(161, 'groom_mother_citizenship', 'text'),
(162, 'groom_mother_residence', 'text'),
(163, 'groom_consent_person', 'text'),
(164, 'groom_consent_relationship', 'text'),
(165, 'groom_consent_citizenship', 'text'),
(166, 'groom_consent_residence', 'text'),
(167, 'bride_first', 'text'),
(168, 'bride_middle', 'text'),
(169, 'bride_last', 'text'),
(170, 'bride_dob_day', 'text'),
(171, 'bride_dob_month', 'text'),
(172, 'bride_dob_year', 'text'),
(173, 'bride_age', 'text'),
(174, 'bride_pob_city', 'text'),
(175, 'bride_pob_province', 'text'),
(176, 'bride_sex', 'text'),
(177, 'bride_citizenship', 'text'),
(178, 'bride_residence', 'text'),
(179, 'bride_religion', 'text'),
(180, 'bride_civil_status', 'text'),
(181, 'bride_prev_marriage', 'text'),
(182, 'bride_relationship_degree', 'text'),
(183, 'bride_father_first', 'text'),
(184, 'bride_father_middle', 'text'),
(185, 'bride_father_last', 'text'),
(186, 'bride_father_citizenship', 'text'),
(187, 'bride_father_residence', 'text'),
(188, 'bride_mother_first', 'text'),
(189, 'bride_mother_middle', 'text'),
(190, 'bride_mother_last', 'text'),
(191, 'bride_mother_citizenship', 'text'),
(192, 'bride_mother_residence', 'text'),
(193, 'bride_consent_person', 'text'),
(194, 'bride_consent_relationship', 'text'),
(195, 'bride_consent_citizenship', 'text'),
(196, 'bride_consent_residence', 'text'),
(197, 'date_receipt', 'text'),
(198, 'date_issuance', 'text'),
(199, 'processed_by', 'text'),
(200, 'date_processed', 'text'),
(201, 'verified_position', 'text'),
(202, 'issued_to', 'text'),
(203, 'amount_paid', 'text'),
(204, 'or_number', 'text'),
(205, 'date_paid', 'text'),
(206, 'certFormContent', 'text'),
(207, 'form1A', 'text'),
(208, 'f1a_sex', 'text'),
(209, 'f1a_issued_to', 'text'),
(210, 'f1a_verified_pos', 'text'),
(211, 'f1a_amount', 'text'),
(212, 'f1a_or_number', 'text'),
(213, 'f1a_date_paid', 'text'),
(214, 'form2A', 'text'),
(215, 'form3A', 'text'),
(216, 'date_of_birth', 'text'),
(217, 'date_of_marriage_of_parents', 'text'),
(218, 'place_of_birth', 'text'),
(219, 'place_of_marriage_of_parents', 'text'),
(220, 'registry_number', 'text'),
(221, 'nationality_of_mother', 'text'),
(222, 'nationality_of_father', 'text'),
(223, 'f1a_registry', 'text'),
(224, 'city', 'text'),
(225, 'date', 'text'),
(226, 'date_of_registration', 'text'),
(227, 'verified_by', 'text'),
(228, 'child_name', 'text'),
(229, 'mother_name', 'text'),
(230, 'mother_nationality', 'text'),
(231, 'father_name', 'text'),
(232, 'father_nationality', 'text'),
(233, 'parents_marriage_date', 'text'),
(234, 'parents_marriage_place', 'text');

-- --------------------------------------------------------

--
-- Table structure for table `documents`
--

CREATE TABLE `documents` (
  `doc_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `status` varchar(45) NOT NULL DEFAULT 'Pending',
  `mnb_confidence_score` float NOT NULL DEFAULT 0,
  `upload_date` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `documents`
--

INSERT INTO `documents` (`doc_id`, `user_id`, `type_id`, `status`, `mnb_confidence_score`, `upload_date`) VALUES
(1, 1, 1, 'Approved', 0.96, '2025-01-10 09:00:00'),
(2, 1, 1, 'Pending', 0.94, '2025-01-15 10:30:00'),
(3, 1, 1, 'Pending', 0.91, '2025-02-03 08:45:00'),
(4, 1, 1, 'Pending', 0, '2025-03-07 11:00:00'),
(5, 1, 2, 'Approved', 0.95, '2025-02-14 14:00:00'),
(6, 1, 2, 'Rejected', 0.88, '2025-03-01 09:15:00'),
(7, 1, 3, 'Approved', 0.97, '2025-01-28 13:00:00'),
(8, 1, 3, 'Pending', 0.93, '2025-02-20 10:00:00'),
(9, 1, 4, 'Pending', 0.92, '2025-03-05 08:00:00'),
(10, 1, 4, 'Approved', 0.96, '2025-03-06 09:30:00'),
(11, 1, 1, 'Pending', 0, '2026-03-12 17:51:59'),
(12, 1, 1, 'Pending', 0, '2026-03-12 17:53:21'),
(13, 1, 1, 'Pending', 0, '2026-03-12 17:58:26'),
(14, 1, 1, 'Pending', 0, '2026-03-12 18:03:00'),
(15, 1, 1, 'Pending', 0, '2026-03-12 18:07:03'),
(16, 1, 1, 'Pending', 0, '2026-03-12 22:02:53'),
(17, 1, 1, 'Pending', 0, '2026-03-12 22:03:48'),
(18, 1, 1, 'Pending', 0, '2026-03-12 22:07:39'),
(19, 1, 1, 'Pending', 0, '2026-03-12 22:07:59'),
(20, 1, 1, 'Pending', 0, '2026-03-12 22:08:58'),
(21, 1, 1, 'Pending', 0, '2026-03-12 22:12:45'),
(22, 1, 1, 'Pending', 0, '2026-03-13 19:01:01'),
(23, 1, 1, 'Pending', 0, '2026-03-13 19:02:05'),
(24, 1, 1, 'Pending', 0, '2026-03-13 19:03:09'),
(25, 1, 1, 'Pending', 0, '2026-03-13 19:03:41'),
(26, 1, 1, 'Pending', 0, '2026-03-13 19:06:08'),
(27, 1, 1, 'Pending', 0, '2026-03-13 19:19:28'),
(28, 1, 1, 'Pending', 0, '2026-03-13 19:47:21'),
(29, 1, 1, 'Pending', 0, '2026-03-13 19:48:26'),
(30, 1, 1, 'Pending', 0, '2026-03-13 19:48:43'),
(31, 1, 1, 'Pending', 0, '2026-03-13 19:48:56'),
(32, 1, 1, 'Pending', 0, '2026-03-13 19:49:16');

-- --------------------------------------------------------

--
-- Table structure for table `document_data`
--

CREATE TABLE `document_data` (
  `data_id` int(11) NOT NULL,
  `doc_id` int(11) NOT NULL,
  `field_id` int(11) NOT NULL,
  `extracted_value` varchar(255) NOT NULL,
  `ner_confidence_score` float NOT NULL DEFAULT 0,
  `is_corrected` tinyint(4) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `document_data`
--

INSERT INTO `document_data` (`data_id`, `doc_id`, `field_id`, `extracted_value`, `ner_confidence_score`, `is_corrected`) VALUES
(1, 1, 1, '2026-BC-00123', 0.99, 0),
(2, 1, 3, 'Tarlac City', 0.99, 0),
(3, 1, 2, 'Tarlac', 0.99, 0),
(4, 1, 4, 'Maria Luisa', 0.97, 0),
(5, 1, 5, 'Dela Cruz', 0.95, 0),
(6, 1, 6, 'Santos', 0.97, 0),
(7, 1, 7, 'Female', 0.99, 0),
(8, 1, 8, '10', 0.98, 0),
(9, 1, 9, 'January', 0.97, 0),
(10, 1, 10, '2026', 0.99, 0),
(11, 1, 12, 'Tarlac City', 0.91, 0),
(12, 1, 13, 'Tarlac', 0.91, 0),
(13, 1, 18, 'Rosa', 0.96, 0),
(14, 1, 19, 'Reyes', 0.95, 0),
(15, 1, 20, 'Dela Cruz', 0.96, 0),
(16, 1, 21, 'Filipino', 0.98, 0),
(17, 1, 29, 'Juan Pedro', 0.94, 0),
(18, 1, 31, 'Santos', 0.94, 0),
(19, 1, 32, 'Filipino', 0.98, 0),
(20, 1, 39, 'June', 0.89, 0),
(21, 1, 40, '12', 0.89, 0),
(22, 1, 41, '2020', 0.9, 0),
(23, 1, 42, 'Tarlac City', 0.87, 0),
(24, 1, 43, 'Tarlac', 0.87, 0),
(25, 1, 45, 'January 15, 2026', 0.97, 0),
(26, 1, 199, 'John Doe', 0.93, 0),
(27, 1, 201, 'City Civil Registrar', 0.95, 0),
(28, 1, 202, 'Rosa Reyes Dela Cruz', 0.96, 0),
(29, 1, 203, '75.00', 1, 0),
(30, 1, 204, 'OR-2026-00456', 1, 0),
(31, 1, 205, 'March 11, 2026', 1, 0),
(32, 1, 198, 'March 11, 2026', 1, 0),
(33, 2, 1, '2026-BC-00124', 0.99, 0),
(34, 2, 3, 'Paniqui', 0.99, 0),
(35, 2, 4, 'Jose', 0.95, 0),
(36, 2, 5, '', 0, 0),
(37, 2, 6, 'Reyes', 0.95, 0),
(38, 2, 7, 'Male', 0.99, 0),
(39, 2, 8, '5', 0.97, 0),
(40, 2, 9, 'February', 0.96, 0),
(41, 2, 10, '2026', 0.99, 0),
(42, 2, 12, 'Paniqui', 0.9, 0),
(43, 2, 13, 'Tarlac', 0.9, 0),
(44, 2, 18, 'Lourdes', 0.94, 0),
(45, 2, 19, 'Cruz', 0.93, 0),
(46, 2, 20, 'Reyes', 0.94, 0),
(47, 2, 21, 'Filipino', 0.98, 0),
(48, 2, 29, 'Antonio', 0.92, 0),
(49, 2, 31, 'Reyes', 0.92, 0),
(50, 2, 32, 'Filipino', 0.98, 0),
(51, 2, 45, 'February 10, 2026', 0.96, 0),
(52, 2, 199, 'Jane Smith', 0.91, 0),
(53, 2, 201, 'Municipal Civil Registrar', 0.93, 0),
(54, 3, 1, '2026-BC-00125', 0.99, 0),
(55, 3, 3, 'Gerona', 0.99, 0),
(56, 3, 4, 'Ana Marie', 0.96, 0),
(57, 3, 5, 'Santos', 0.94, 0),
(58, 3, 6, 'Dela Cruz', 0.96, 0),
(59, 3, 7, 'Female', 0.99, 0),
(60, 3, 8, '1', 0.97, 0),
(61, 3, 9, 'March', 0.96, 0),
(62, 3, 10, '2026', 0.99, 0),
(63, 3, 12, 'Gerona', 0.88, 0),
(64, 3, 13, 'Tarlac', 0.88, 0),
(65, 3, 18, 'Carmen', 0.93, 0),
(66, 3, 19, 'Santos', 0.92, 0),
(67, 3, 20, 'Dela Cruz', 0.93, 0),
(68, 3, 21, 'Filipino', 0.98, 0),
(69, 3, 29, 'Roberto', 0.91, 0),
(70, 3, 31, 'Dela Cruz', 0.91, 0),
(71, 3, 32, 'Filipino', 0.98, 0),
(72, 4, 1, '2026-BC-00126', 0.99, 0),
(73, 4, 3, 'Tarlac City', 0.99, 0),
(74, 5, 1, '2026-DC-00045', 0.99, 0),
(75, 5, 3, 'Tarlac City', 0.99, 0),
(76, 5, 47, 'Roberto', 0.96, 0),
(77, 5, 48, 'Cruz', 0.95, 0),
(78, 5, 49, 'Villanueva', 0.96, 0),
(79, 5, 7, 'Male', 0.99, 0),
(80, 5, 51, '72', 0.99, 0),
(81, 5, 64, 'Married', 0.97, 0),
(82, 5, 60, 'Filipino', 0.99, 0),
(83, 5, 57, '28', 0.95, 0),
(84, 5, 58, 'January', 0.95, 0),
(85, 5, 59, '2026', 0.99, 0),
(86, 5, 54, 'Tarlac Provincial Hospital', 0.92, 0),
(87, 5, 55, 'Tarlac City', 0.92, 0),
(88, 5, 66, 'Cardiopulmonary Arrest', 0.88, 0),
(89, 5, 45, 'February 1, 2026', 0.96, 0),
(90, 5, 199, 'John Doe', 0.93, 0),
(91, 5, 201, 'City Civil Registrar', 0.95, 0),
(92, 5, 202, 'Maria Villanueva', 0.94, 0),
(93, 5, 198, 'March 11, 2026', 1, 0),
(94, 6, 1, '2026-DC-00046', 0.99, 0),
(95, 6, 3, 'Sta. Ignacia', 0.99, 0),
(96, 6, 47, 'Lourdes', 0.91, 0),
(97, 6, 48, 'Santos', 0.9, 0),
(98, 6, 49, 'Magno', 0.91, 0),
(99, 6, 7, 'Female', 0.99, 0),
(100, 6, 51, '65', 0.98, 0),
(101, 6, 64, 'Widowed', 0.9, 0),
(102, 6, 57, '20', 0.93, 0),
(103, 6, 58, 'February', 0.93, 0),
(104, 6, 59, '2026', 0.99, 0),
(105, 6, 55, 'Sta. Ignacia', 0.89, 0),
(106, 6, 56, 'Tarlac', 0.89, 0),
(107, 7, 1, '2026-MC-00078', 0.99, 0),
(108, 7, 3, 'Tarlac City', 0.99, 0),
(109, 7, 80, 'Carlos Miguel', 0.96, 0),
(110, 7, 82, 'Bautista', 0.96, 0),
(111, 7, 86, '28', 0.99, 0),
(112, 7, 90, 'Filipino', 0.99, 0),
(113, 7, 97, 'Lourdes', 0.93, 0),
(114, 7, 98, 'Bautista', 0.93, 0),
(115, 7, 94, 'Ramon', 0.94, 0),
(116, 7, 95, 'Bautista', 0.94, 0),
(117, 7, 103, 'Elena Grace', 0.95, 0),
(118, 7, 105, 'Reyes', 0.95, 0),
(119, 7, 109, '26', 0.99, 0),
(120, 7, 113, 'Filipino', 0.99, 0),
(121, 7, 120, 'Susan', 0.92, 0),
(122, 7, 121, 'Reyes', 0.92, 0),
(123, 7, 117, 'Eduardo', 0.93, 0),
(124, 7, 118, 'Reyes', 0.93, 0),
(125, 7, 129, '14', 0.97, 0),
(126, 7, 130, 'February', 0.97, 0),
(127, 7, 131, '2026', 0.97, 0),
(128, 7, 127, 'Tarlac City', 0.91, 0),
(129, 7, 126, 'Saint John Parish', 0.91, 0),
(130, 7, 45, 'March 1, 2026', 0.96, 0),
(131, 7, 199, 'John Doe', 0.93, 0),
(132, 7, 201, 'City Civil Registrar', 0.95, 0),
(133, 7, 202, 'Carlos Miguel Bautista', 0.95, 0),
(134, 7, 198, 'March 11, 2026', 1, 0),
(135, 8, 1, '2026-MC-00079', 0.99, 0),
(136, 8, 3, 'Paniqui', 0.99, 0),
(137, 8, 80, 'Ramon Jose', 0.94, 0),
(138, 8, 82, 'Dizon', 0.94, 0),
(139, 8, 103, 'Sofia Marie', 0.95, 0),
(140, 8, 105, 'Cruz', 0.95, 0),
(141, 8, 129, '5', 0.96, 0),
(142, 8, 130, 'March', 0.96, 0),
(143, 8, 131, '2026', 0.99, 0),
(144, 8, 127, 'Paniqui', 0.9, 0),
(145, 9, 1, '2026-ML-00031', 0.99, 0),
(146, 9, 3, 'Tarlac City', 0.99, 0),
(147, 9, 137, 'Paolo Gabriel', 0.95, 0),
(148, 9, 139, 'Mendoza', 0.95, 0),
(149, 9, 167, 'Kristine Ann', 0.94, 0),
(150, 9, 169, 'Santos', 0.94, 0),
(151, 9, 129, '10', 0.93, 0),
(152, 9, 130, 'April', 0.93, 0),
(153, 9, 131, '2026', 0.99, 0),
(154, 9, 127, 'Tarlac City', 0.91, 0),
(155, 10, 1, '2026-ML-00032', 0.99, 0),
(156, 10, 3, 'Gerona', 0.99, 0),
(157, 10, 137, 'Angelo Rafael', 0.96, 0),
(158, 10, 139, 'Torres', 0.96, 0),
(159, 10, 167, 'Camille Rose', 0.95, 0),
(160, 10, 169, 'Garcia', 0.95, 0),
(161, 10, 129, '20', 0.94, 0),
(162, 10, 130, 'March', 0.94, 0),
(163, 10, 131, '2026', 0.99, 0),
(164, 10, 127, 'Gerona', 0.89, 0),
(165, 10, 203, '75.00', 1, 0),
(166, 10, 204, 'OR-2026-00458', 1, 0),
(167, 10, 205, 'March 11, 2026', 1, 0),
(168, 10, 198, 'March 11, 2026', 1, 0),
(200, 11, 203, '75.00', 0, 0),
(201, 11, 4, 'Maria Luisa', 0.97, 0),
(202, 11, 6, 'Santos', 0.97, 0),
(203, 11, 5, 'Dela Cruz', 0.95, 0),
(204, 11, 3, 'Tarlac City', 0, 0),
(205, 11, 198, 'March 12, 2026', 0, 0),
(206, 11, 205, 'March 12, 2026', 0, 0),
(207, 11, 45, 'January 15, 2026', 0.97, 0),
(208, 11, 8, '10', 0.98, 0),
(209, 11, 9, 'January', 0.97, 0),
(210, 11, 10, '2026', 0.99, 0),
(211, 11, 32, 'Filipino', 0.98, 0),
(212, 11, 29, 'Juan Pedro', 0.94, 0),
(213, 11, 31, 'Santos', 0.94, 0),
(214, 11, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(215, 11, 23, '28', 0, 0),
(216, 11, 21, 'Filipino', 0.98, 0),
(217, 11, 18, 'Rosa', 0.96, 0),
(218, 11, 20, 'Dela Cruz', 0.96, 0),
(219, 11, 19, 'Reyes', 0, 0),
(220, 11, 204, 'OR-2026-00456', 0, 0),
(221, 11, 42, 'Tarlac City', 0.87, 0),
(222, 11, 40, '12', 0, 0),
(223, 11, 39, 'June', 0.89, 0),
(224, 11, 43, 'Tarlac', 0, 0),
(225, 11, 41, '2020', 0, 0),
(226, 11, 12, 'Tarlac City', 0.91, 0),
(227, 11, 13, 'Tarlac', 0.91, 0),
(228, 11, 46, 'Dr. Jose Reyes', 0, 0),
(229, 11, 199, 'John Doe', 0, 0),
(230, 11, 2, 'Tarlac', 0, 0),
(231, 11, 1, '2026-BC-00123', 0.99, 0),
(232, 11, 7, 'Female', 0.99, 0),
(233, 11, 201, 'City Civil Registrar', 0, 0),
(234, 11, 206, 'LCR Form No. 1A(Birth available)\n                                \n                                    Republic of the Philippines\n                                    Office of the City Registrar\n                                    \n                       ', 0, 1),
(235, 11, 207, 'LCR Form No. 1A(Birth available)\n                                \n                                    Republic of the Philippines\n                                    Office of the City Registrar\n                                    \n                       ', 0, 1),
(236, 11, 208, 'Female', 0, 1),
(237, 11, 209, 'Rosa Reyes Dela Cruz', 0, 1),
(238, 11, 210, 'City Civil Registrar', 0, 1),
(239, 11, 211, '75.00', 0, 1),
(240, 11, 212, 'OR-2026-00456', 0, 1),
(241, 11, 213, 'March 12, 2026', 0, 1),
(242, 11, 214, 'LCR Form No. 2A(Death available)\n                                \n                                    Republic of the Philippines\n                                    Office of the City Registrar\n                                    \n                       ', 0, 1),
(243, 11, 215, 'LCR Form No. 3A(Marriage available)\n                                \n                                    Republic of the Philippines\n                                    Office of the City Registrar\n                                    \n                    ', 0, 1),
(244, 12, 203, '75.00', 0, 1),
(245, 12, 4, 'Maria Luisa', 0.97, 0),
(246, 12, 6, 'Santos', 0.97, 0),
(247, 12, 5, 'Dela Cruz', 0.95, 0),
(248, 12, 3, 'Tarlac City', 0, 0),
(249, 12, 198, 'March 12, 2026', 0, 0),
(250, 12, 205, 'March 12, 2026', 0, 1),
(251, 12, 45, 'January 15, 2026', 0.97, 0),
(252, 12, 8, '10', 0.98, 0),
(253, 12, 9, 'January', 0.97, 0),
(254, 12, 10, '2026', 0.99, 0),
(255, 12, 32, 'Filipino', 0.98, 0),
(256, 12, 29, 'Juan Pedro', 0.94, 0),
(257, 12, 31, 'Santos', 0.94, 0),
(258, 12, 202, 'Rosa Reyes Dela Cruz', 0, 1),
(259, 12, 23, '28', 0, 0),
(260, 12, 21, 'Filipino', 0.98, 0),
(261, 12, 18, 'Rosa', 0.96, 0),
(262, 12, 20, 'Dela Cruz', 0.96, 0),
(263, 12, 19, 'Reyes', 0, 0),
(264, 12, 204, 'OR-2026-00456', 0, 1),
(265, 12, 42, 'Tarlac City', 0.87, 0),
(266, 12, 40, '12', 0, 0),
(267, 12, 39, 'June', 0.89, 0),
(268, 12, 43, 'Tarlac', 0, 0),
(269, 12, 41, '2020', 0, 0),
(270, 12, 12, 'Tarlac City', 0.91, 0),
(271, 12, 13, 'Tarlac', 0.91, 0),
(272, 12, 46, 'Dr. Jose Reyes', 0, 0),
(273, 12, 199, 'John Doe', 0, 0),
(274, 12, 2, 'Tarlac', 0, 0),
(275, 12, 1, '2026-BC-00123', 0.99, 0),
(276, 12, 7, 'Female', 0.99, 1),
(277, 12, 201, 'City Civil Registrar', 0, 1),
(278, 13, 203, '75.00', 0, 0),
(279, 13, 4, 'Maria Luisa', 0.97, 0),
(280, 13, 6, 'Santos', 0.97, 0),
(281, 13, 5, 'Dela Cruz', 0.95, 0),
(282, 13, 3, 'Tarlac City', 0, 0),
(283, 13, 198, 'March 12, 2026', 0, 0),
(284, 13, 205, 'March 12, 2026', 0, 0),
(285, 13, 45, 'January 15, 2026', 0.97, 0),
(286, 13, 8, '10', 0.98, 0),
(287, 13, 9, 'January', 0.97, 0),
(288, 13, 10, '2026', 0.99, 0),
(289, 13, 32, 'Filipino', 0.98, 0),
(290, 13, 29, 'Juan Pedro', 0.94, 0),
(291, 13, 31, 'Santos', 0.94, 0),
(292, 13, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(293, 13, 23, '28', 0, 0),
(294, 13, 21, 'Filipino', 0.98, 0),
(295, 13, 18, 'Rosa', 0.96, 0),
(296, 13, 20, 'Dela Cruz', 0.96, 0),
(297, 13, 19, 'Reyes', 0, 0),
(298, 13, 204, 'OR-2026-00456', 0, 0),
(299, 13, 42, 'Tarlac City', 0.87, 0),
(300, 13, 40, '12', 0, 0),
(301, 13, 39, 'June', 0.89, 0),
(302, 13, 43, 'Tarlac', 0, 0),
(303, 13, 41, '2020', 0, 0),
(304, 13, 12, 'Tarlac City', 0.91, 0),
(305, 13, 13, 'Tarlac', 0.91, 0),
(306, 13, 46, 'Dr. Jose Reyes', 0, 0),
(307, 13, 199, 'John Doe', 0, 0),
(308, 13, 2, 'Tarlac', 0, 0),
(309, 13, 1, '2026-BC-00123', 0.99, 0),
(310, 13, 7, 'Female', 0.99, 0),
(311, 13, 201, 'City Civil Registrar', 0, 0),
(312, 14, 203, '75.00', 0, 0),
(313, 14, 4, 'Maria Luisa', 0.97, 0),
(314, 14, 6, 'Santos', 0.97, 0),
(315, 14, 5, 'Dela Cruz', 0.95, 0),
(316, 14, 3, 'Tarlac City', 0, 0),
(317, 14, 198, 'March 12, 2026', 0, 0),
(318, 14, 205, 'March 12, 2026', 0, 0),
(319, 14, 45, 'January 15, 2026', 0.97, 0),
(320, 14, 8, '10', 0.98, 0),
(321, 14, 9, 'January', 0.97, 0),
(322, 14, 10, '2026', 0.99, 0),
(323, 14, 32, 'Filipino', 0.98, 0),
(324, 14, 29, 'Juan Pedro', 0.94, 0),
(325, 14, 31, 'Santos', 0.94, 0),
(326, 14, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(327, 14, 23, '28', 0, 0),
(328, 14, 21, 'Filipino', 0.98, 0),
(329, 14, 18, 'Rosa', 0.96, 0),
(330, 14, 20, 'Dela Cruz', 0.96, 0),
(331, 14, 19, 'Reyes', 0, 0),
(332, 14, 204, 'OR-2026-00456', 0, 0),
(333, 14, 42, 'Tarlac City', 0.87, 0),
(334, 14, 40, '12', 0, 0),
(335, 14, 39, 'June', 0.89, 0),
(336, 14, 43, 'Tarlac', 0, 0),
(337, 14, 41, '2020', 0, 0),
(338, 14, 12, 'Tarlac City', 0.91, 0),
(339, 14, 13, 'Tarlac', 0.91, 0),
(340, 14, 46, 'Dr. Jose Reyes', 0, 0),
(341, 14, 199, 'John Doe', 0, 0),
(342, 14, 2, 'Tarlac', 0, 0),
(343, 14, 1, '2026-BC-00123', 0.99, 0),
(344, 14, 7, 'Female', 0.99, 0),
(345, 14, 201, 'City Civil Registrar', 0, 0),
(346, 15, 203, '75.00', 0, 0),
(347, 15, 4, 'Maria Luisa', 0.97, 0),
(348, 15, 6, 'Santos', 0.97, 0),
(349, 15, 5, 'Dela Cruz', 0.95, 0),
(350, 15, 3, 'Tarlac City', 0, 0),
(351, 15, 198, 'March 12, 2026', 0, 0),
(352, 15, 205, 'March 12, 2026', 0, 0),
(353, 15, 45, 'January 15, 2026', 0.97, 0),
(354, 15, 8, '10', 0.98, 0),
(355, 15, 9, 'January', 0.97, 0),
(356, 15, 10, '2026', 0.99, 0),
(357, 15, 32, 'Filipino', 0.98, 0),
(358, 15, 29, 'Juan Pedro', 0.94, 0),
(359, 15, 31, 'Santos', 0.94, 0),
(360, 15, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(361, 15, 23, '28', 0, 0),
(362, 15, 21, 'Filipino', 0.98, 0),
(363, 15, 18, 'Rosa', 0.96, 0),
(364, 15, 20, 'Dela Cruz', 0.96, 0),
(365, 15, 19, 'Reyes', 0, 0),
(366, 15, 204, 'OR-2026-00456', 0, 0),
(367, 15, 42, 'Tarlac City', 0.87, 0),
(368, 15, 40, '12', 0, 0),
(369, 15, 39, 'June', 0.89, 0),
(370, 15, 43, 'Tarlac', 0, 0),
(371, 15, 41, '2020', 0, 0),
(372, 15, 12, 'Tarlac City', 0.91, 0),
(373, 15, 13, 'Tarlac', 0.91, 0),
(374, 15, 46, 'Dr. Jose Reyes', 0, 0),
(375, 15, 199, 'John Doe', 0, 0),
(376, 15, 2, 'Tarlac', 0, 0),
(377, 15, 1, '2026-BC-00123', 0.99, 0),
(378, 15, 7, 'Female', 0.99, 0),
(379, 15, 201, 'City Civil Registrar', 0, 0),
(380, 16, 203, '75.00', 0, 0),
(381, 16, 4, 'Maria Luisa', 0.97, 0),
(382, 16, 6, 'Santos', 0.97, 0),
(383, 16, 5, 'Dela Cruz', 0.95, 0),
(384, 16, 3, 'Tarlac City', 0, 0),
(385, 16, 198, 'March 12, 2026', 0, 0),
(386, 16, 205, 'March 12, 2026', 0, 0),
(387, 16, 45, 'January 15, 2026', 0.97, 0),
(388, 16, 8, '10', 0.98, 0),
(389, 16, 9, 'January', 0.97, 0),
(390, 16, 10, '2026', 0.99, 0),
(391, 16, 32, 'Filipino', 0.98, 0),
(392, 16, 29, 'Juan Pedro', 0.94, 0),
(393, 16, 31, 'Santos', 0.94, 0),
(394, 16, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(395, 16, 23, '28', 0, 0),
(396, 16, 21, 'Filipino', 0.98, 0),
(397, 16, 18, 'Rosa', 0.96, 0),
(398, 16, 20, 'Dela Cruz', 0.96, 0),
(399, 16, 19, 'Reyes', 0, 0),
(400, 16, 204, 'OR-2026-00456', 0, 0),
(401, 16, 42, 'Tarlac City', 0.87, 0),
(402, 16, 40, '12', 0, 0),
(403, 16, 39, 'June', 0.89, 0),
(404, 16, 43, 'Tarlac', 0, 0),
(405, 16, 41, '2020', 0, 0),
(406, 16, 12, 'Tarlac City', 0.91, 0),
(407, 16, 13, 'Tarlac', 0.91, 0),
(408, 16, 46, 'Dr. Jose Reyes', 0, 0),
(409, 16, 199, 'John Doe', 0, 0),
(410, 16, 2, 'Tarlac', 0, 0),
(411, 16, 1, '2026-BC-00123', 0.99, 0),
(412, 16, 7, 'Female', 0.99, 0),
(413, 16, 201, 'City Civil Registrar', 0, 0),
(414, 17, 203, '75.00', 0, 0),
(415, 17, 4, 'Maria Luisa', 0.97, 0),
(416, 17, 6, 'Santos', 0.97, 0),
(417, 17, 5, 'Dela Cruz', 0.95, 0),
(418, 17, 3, 'Tarlac City', 0, 0),
(419, 17, 198, 'March 12, 2026', 0, 0),
(420, 17, 205, 'March 12, 2026', 0, 0),
(421, 17, 45, 'January 15, 2026', 0.97, 0),
(422, 17, 8, '10', 0.98, 0),
(423, 17, 9, 'January', 0.97, 0),
(424, 17, 10, '2026', 0.99, 0),
(425, 17, 32, 'Filipino', 0.98, 0),
(426, 17, 29, 'Juan Pedro', 0.94, 0),
(427, 17, 31, 'Santos', 0.94, 0),
(428, 17, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(429, 17, 23, '28', 0, 0),
(430, 17, 21, 'Filipino', 0.98, 0),
(431, 17, 18, 'Rosa', 0.96, 0),
(432, 17, 20, 'Dela Cruz', 0.96, 0),
(433, 17, 19, 'Reyes', 0, 0),
(434, 17, 204, 'OR-2026-00456', 0, 0),
(435, 17, 42, 'Tarlac City', 0.87, 0),
(436, 17, 40, '12', 0, 0),
(437, 17, 39, 'June', 0.89, 0),
(438, 17, 43, 'Tarlac', 0, 0),
(439, 17, 41, '2020', 0, 0),
(440, 17, 12, 'Tarlac City', 0.91, 0),
(441, 17, 13, 'Tarlac', 0.91, 0),
(442, 17, 46, 'Dr. Jose Reyes', 0, 0),
(443, 17, 199, 'John Doe', 0, 0),
(444, 17, 2, 'Tarlac', 0, 0),
(445, 17, 1, '2026-BC-00123', 0.99, 0),
(446, 17, 7, 'Female', 0.99, 0),
(447, 17, 201, 'City Civil Registrar', 0, 0),
(448, 18, 203, '75.00', 0, 0),
(449, 18, 4, 'Maria Luisa', 0.97, 0),
(450, 18, 6, 'Santos', 0.97, 0),
(451, 18, 5, 'Dela Cruz', 0.95, 0),
(452, 18, 3, 'Tarlac City', 0, 0),
(453, 18, 198, 'March 12, 2026', 0, 0),
(454, 18, 205, 'March 12, 2026', 0, 0),
(455, 18, 45, 'January 15, 2026', 0.97, 0),
(456, 18, 8, '10', 0.98, 0),
(457, 18, 9, 'January', 0.97, 0),
(458, 18, 10, '2026', 0.99, 0),
(459, 18, 32, 'Filipino', 0.98, 0),
(460, 18, 29, 'Juan Pedro', 0.94, 0),
(461, 18, 31, 'Santos', 0.94, 0),
(462, 18, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(463, 18, 23, '28', 0, 0),
(464, 18, 21, 'Filipino', 0.98, 0),
(465, 18, 18, 'Rosa', 0.96, 0),
(466, 18, 20, 'Dela Cruz', 0.96, 0),
(467, 18, 19, 'Reyes', 0, 0),
(468, 18, 204, 'OR-2026-00456', 0, 0),
(469, 18, 42, 'Tarlac City', 0.87, 0),
(470, 18, 40, '12', 0, 0),
(471, 18, 39, 'June', 0.89, 0),
(472, 18, 43, 'Tarlac', 0, 0),
(473, 18, 41, '2020', 0, 0),
(474, 18, 12, 'Tarlac City', 0.91, 0),
(475, 18, 13, 'Tarlac', 0.91, 0),
(476, 18, 46, 'Dr. Jose Reyes', 0, 0),
(477, 18, 199, 'John Doe', 0, 0),
(478, 18, 2, 'Tarlac', 0, 0),
(479, 18, 1, '2026-BC-00123', 0.99, 0),
(480, 18, 7, 'Female', 0.99, 0),
(481, 18, 201, 'City Civil Registrar', 0, 0),
(482, 19, 203, '75.00', 0, 0),
(483, 19, 4, 'Maria Luisa', 0.97, 0),
(484, 19, 6, 'Santos', 0.97, 0),
(485, 19, 5, 'Dela Cruz', 0.95, 0),
(486, 19, 3, 'Tarlac City', 0, 0),
(487, 19, 198, 'March 12, 2026', 0, 0),
(488, 19, 205, 'March 12, 2026', 0, 0),
(489, 19, 45, 'January 15, 2026', 0.97, 0),
(490, 19, 8, '10', 0.98, 0),
(491, 19, 9, 'January', 0.97, 0),
(492, 19, 10, '2026', 0.99, 0),
(493, 19, 32, 'Filipino', 0.98, 0),
(494, 19, 29, 'Juan Pedro', 0.94, 0),
(495, 19, 31, 'Santos', 0.94, 0),
(496, 19, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(497, 19, 23, '28', 0, 0),
(498, 19, 21, 'Filipino', 0.98, 0),
(499, 19, 18, 'Rosa', 0.96, 0),
(500, 19, 20, 'Dela Cruz', 0.96, 0),
(501, 19, 19, 'Reyes', 0, 0),
(502, 19, 204, 'OR-2026-00456', 0, 0),
(503, 19, 42, 'Tarlac City', 0.87, 0),
(504, 19, 40, '12', 0, 0),
(505, 19, 39, 'June', 0.89, 0),
(506, 19, 43, 'Tarlac', 0, 0),
(507, 19, 41, '2020', 0, 0),
(508, 19, 12, 'Tarlac City', 0.91, 0),
(509, 19, 13, 'Tarlac', 0.91, 0),
(510, 19, 46, 'Dr. Jose Reyes', 0, 0),
(511, 19, 199, 'John Doe', 0, 0),
(512, 19, 2, 'Tarlac', 0, 0),
(513, 19, 1, '2026-BC-00123', 0.99, 0),
(514, 19, 7, 'Female', 0.99, 0),
(515, 19, 201, 'City Civil Registrar', 0, 0),
(516, 20, 203, '75.00', 0, 0),
(517, 20, 4, 'Maria Luisa', 0.97, 0),
(518, 20, 6, 'Santos', 0.97, 0),
(519, 20, 5, 'Dela Cruz', 0.95, 0),
(520, 20, 3, 'Tarlac City', 0, 0),
(521, 20, 198, 'March 12, 2026', 0, 0),
(522, 20, 205, 'March 12, 2026', 0, 0),
(523, 20, 45, 'January 15, 2026', 0.97, 0),
(524, 20, 8, '10', 0.98, 0),
(525, 20, 9, 'January', 0.97, 0),
(526, 20, 10, '2026', 0.99, 0),
(527, 20, 32, 'Filipino', 0.98, 0),
(528, 20, 29, 'Juan Pedro', 0.94, 0),
(529, 20, 31, 'Santos', 0.94, 0),
(530, 20, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(531, 20, 23, '28', 0, 0),
(532, 20, 21, 'Filipino', 0.98, 0),
(533, 20, 18, 'Rosa', 0.96, 0),
(534, 20, 20, 'Dela Cruz', 0.96, 0),
(535, 20, 19, 'Reyes', 0, 0),
(536, 20, 204, 'OR-2026-00456', 0, 0),
(537, 20, 42, 'Tarlac City', 0.87, 0),
(538, 20, 40, '12', 0, 0),
(539, 20, 39, 'June', 0.89, 0),
(540, 20, 43, 'Tarlac', 0, 0),
(541, 20, 41, '2020', 0, 0),
(542, 20, 12, 'Tarlac City', 0.91, 0),
(543, 20, 13, 'Tarlac', 0.91, 0),
(544, 20, 46, 'Dr. Jose Reyes', 0, 0),
(545, 20, 199, 'John Doe', 0, 0),
(546, 20, 2, 'Tarlac', 0, 0),
(547, 20, 1, '2026-BC-00123', 0.99, 0),
(548, 20, 7, 'Female', 0.99, 0),
(549, 20, 201, 'City Civil Registrar', 0, 0),
(550, 21, 203, '75.00', 0, 0),
(551, 21, 4, 'Maria Luisa', 0.97, 0),
(552, 21, 6, 'Santos', 0.97, 0),
(553, 21, 5, 'Dela Cruz', 0.95, 0),
(554, 21, 3, 'Tarlac City', 0, 0),
(555, 21, 198, 'March 12, 2026', 0, 0),
(556, 21, 205, 'March 12, 2026', 0, 0),
(557, 21, 45, 'January 15, 2026', 0.97, 0),
(558, 21, 8, '10', 0.98, 0),
(559, 21, 9, 'January', 0.97, 0),
(560, 21, 10, '2026', 0.99, 0),
(561, 21, 32, 'Filipino', 0.98, 0),
(562, 21, 29, 'Juan Pedro', 0.94, 0),
(563, 21, 31, 'Santos', 0.94, 0),
(564, 21, 202, 'Rosa Reyes Dela Cruz', 0, 0),
(565, 21, 23, '28', 0, 0),
(566, 21, 21, 'Filipino', 0.98, 0),
(567, 21, 18, 'Rosa', 0.96, 0),
(568, 21, 20, 'Dela Cruz', 0.96, 0),
(569, 21, 19, 'Reyes', 0, 0),
(570, 21, 204, 'OR-2026-00456', 0, 0),
(571, 21, 42, 'Tarlac City', 0.87, 0),
(572, 21, 40, '12', 0, 0),
(573, 21, 39, 'June', 0.89, 0),
(574, 21, 43, 'Tarlac', 0, 0),
(575, 21, 41, '2020', 0, 0),
(576, 21, 12, 'Tarlac City', 0.91, 0),
(577, 21, 13, 'Tarlac', 0.91, 0),
(578, 21, 46, 'Dr. Jose Reyes', 0, 0),
(579, 21, 199, 'John Doe', 0, 0),
(580, 21, 2, 'Tarlac', 0, 0),
(581, 21, 1, '2026-BC-00123', 0.99, 0),
(582, 21, 7, 'Female', 0.99, 0),
(583, 21, 201, 'City Civil Registrar', 0, 0),
(584, 22, 216, 'fpayyMonth, 1Year', 0.9, 0),
(585, 22, 217, 'DArEMonth fDpay, 1Year', 0.9, 0),
(586, 22, 218, 'aiR  ensaaranga ciicipaii Rice', 0.9, 0),
(587, 22, 219, 'b PAcE1city / Municipality0 fProvinca', 0.9, 0),
(588, 22, 1, 'RegistryNo', 0, 0),
(589, 22, 220, 'RegistryNo', 0.9, 0),
(590, 22, 7, 'Setaeemae', 0.9, 0),
(591, 23, 216, 'dTsFo o, SReuse ouL7', 0.9, 0),
(592, 23, 217, 'L crlte 3 St, mitarm5', 0.9, 0),
(593, 23, 221, 'TREsTDETET', 0.9, 0),
(594, 23, 219, 'geneam1 Others specifyy L B6', 0.9, 0),
(595, 23, 7, '1CaMegatgE', 0.9, 0),
(596, 24, 216, 'The civil Rgisrar, L', 0.9, 0),
(597, 24, 217, 'Ciicipai i,', 0.9, 0),
(598, 24, 222, 'L', 0.9, 0),
(599, 24, 221, 'E', 0.9, 0),
(600, 24, 218, 'M/ 7 4rpl yir a Jirrue vw coriracr rariaaev 4My Vrpl V 4 /icerae /o corarrad//4ayia /', 0.9, 0),
(601, 24, 219, 'PaeT Pice', 0.9, 0),
(602, 24, 7, 'e civilReistFa', 0.9, 0),
(603, 25, 216, 'The civil Rgisrar, L', 0.9, 0),
(604, 25, 217, 'Ciicipai i,', 0.9, 0),
(605, 25, 222, 'L', 0.9, 0),
(606, 25, 221, 'E', 0.9, 0),
(607, 25, 218, 'M/ 7 4rpl yir a Jirrue vw coriracr rariaaev 4My Vrpl V 4 /icerae /o corarrad//4ayia /', 0.9, 0),
(608, 25, 219, 'PaeT Pice', 0.9, 0),
(609, 25, 7, 'e civilReistFa', 0.9, 0),
(610, 26, 216, '11, 218', 0.9, 0),
(611, 26, 217, 'DArEMonth WPay, Yaar', 0.9, 0),
(612, 26, 221, 'csr', 0.9, 0),
(613, 26, 218, '1aiaeaaaranaaa iiipaif Rie', 0.9, 0),
(614, 26, 219, 'b, PAcsKcity / Municipality0 fProwinca', 0.9, 0),
(615, 26, 1, 'Registry No', 0, 0),
(616, 26, 220, 'Registry No', 0.9, 0),
(617, 26, 7, 'SetaMA', 0.9, 0),
(618, 27, 216, '11, 218', 0.9, 0),
(619, 27, 217, 'DArEMonth WPay, Yaar', 0.9, 0),
(620, 27, 221, 'csr', 0.9, 0),
(621, 27, 218, '1aiaeaaaranaaa iiipaif Rie', 0.9, 0),
(622, 27, 219, 'b, PAcsKcity / Municipality0 fProwinca', 0.9, 0),
(623, 27, 1, 'Registry No', 0, 0),
(624, 27, 220, 'Registry No', 0.9, 0),
(625, 27, 7, 'SetaMA', 0.9, 0),
(626, 28, 216, '11, 218', 0.9, 0),
(627, 28, 217, 'DArEMonth WPay, Yaar', 0.9, 0),
(628, 28, 221, 'csr', 0.9, 0),
(629, 28, 218, '1aiaeaaaranaaa iiipaif Rie', 0.9, 0),
(630, 28, 219, 'b, PAcsKcity / Municipality0 fProwinca', 0.9, 0),
(631, 28, 1, 'Registry No', 0, 0),
(632, 28, 220, 'Registry No', 0.9, 0),
(633, 28, 7, 'SetaMA', 0.9, 0),
(634, 28, 206, 'LCR Form No. 1A(Birth available)\n                                \n                                    Republic of the Philippines\n                                    Office of the City Registrar\n                                    \n                       ', 0, 1),
(635, 28, 207, 'LCR Form No. 1A(Birth available)\n                                \n                                    Republic of the Philippines\n                                    Office of the City Registrar\n                                    \n                       ', 0, 1),
(636, 28, 223, 'Registry No', 0, 1),
(637, 28, 208, 'SetaMA', 0, 1),
(638, 28, 214, 'LCR Form No. 2A(Death available)\n                                \n                                    Republic of the Philippines\n                                    Office of the City Registrar\n                                    \n                       ', 0, 1),
(639, 28, 215, 'LCR Form No. 3A(Marriage available)\n                                \n                                    Republic of the Philippines\n                                    Office of the City Registrar\n                                    \n                    ', 0, 1),
(640, 29, 216, 'dTsFo o, SReuse ouL7', 0.9, 0),
(641, 29, 217, 'L crlte 3 St, mitarm5', 0.9, 0),
(642, 29, 221, 'TREsTDETET', 0.9, 0),
(643, 29, 219, 'geneam1 Others specifyy L B6', 0.9, 0),
(644, 29, 7, '1CaMegatgE', 0.9, 0),
(645, 30, 216, 'E,', 0.9, 0),
(646, 30, 217, ',', 0.9, 0),
(647, 30, 218, 'DBai L', 0.9, 0),
(648, 30, 7, 'ld', 0.9, 0),
(649, 31, 216, 'The civil Rgisrar, L', 0.9, 0),
(650, 31, 217, 'Ciicipai i,', 0.9, 0),
(651, 31, 222, 'L', 0.9, 0),
(652, 31, 221, 'E', 0.9, 0),
(653, 31, 218, 'M/ 7 4rpl yir a Jirrue vw coriracr rariaaev 4My Vrpl V 4 /icerae /o corarrad//4ayia /', 0.9, 0),
(654, 31, 219, 'PaeT Pice', 0.9, 0),
(655, 31, 7, 'e civilReistFa', 0.9, 0),
(656, 32, 216, 'fpayyMonth, 1Year', 0.9, 0),
(657, 32, 217, 'DArEMonth fDpay, 1Year', 0.9, 0),
(658, 32, 218, 'aiR  ensaaranga ciicipaii Rice', 0.9, 0),
(659, 32, 219, 'b PAcE1city / Municipality0 fProvinca', 0.9, 0),
(660, 32, 1, 'RegistryNo', 0, 0),
(661, 32, 220, 'RegistryNo', 0.9, 0),
(662, 32, 7, 'Setaeemae', 0.9, 0),
(663, 12, 220, '2026-BC-00123', 0, 1),
(664, 12, 224, 'Tarlac City', 0, 1),
(665, 12, 225, 'March 12, 2026', 0, 1),
(666, 12, 226, 'January 15, 2026', 0, 1),
(667, 12, 227, 'John Doe', 0, 1),
(668, 12, 228, 'Maria Luisa Dela Cruz Santos', 0, 1),
(669, 12, 216, 'January 10, 2026', 0, 1),
(670, 12, 218, 'Tarlac City, Tarlac', 0, 1),
(671, 12, 229, 'Rosa Reyes Dela Cruz', 0, 1),
(672, 12, 230, 'Filipino', 0, 1),
(673, 12, 231, 'Juan Pedro  Santos', 0, 1),
(674, 12, 232, 'Filipino', 0, 1),
(675, 12, 233, 'June 12, 2020', 0, 1),
(676, 12, 234, 'Tarlac City, Tarlac', 0, 1);

-- --------------------------------------------------------

--
-- Table structure for table `document_types`
--

CREATE TABLE `document_types` (
  `type_id` int(11) NOT NULL,
  `type_code` varchar(45) NOT NULL,
  `type_name` varchar(45) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `document_types`
--

INSERT INTO `document_types` (`type_id`, `type_code`, `type_name`) VALUES
(1, 'BIRTH', 'Birth Certificate'),
(2, 'DEATH', 'Death Certificate'),
(3, 'MARRCERT', 'Marriage Certificate'),
(4, 'MARRLIC', 'Marriage License');

-- --------------------------------------------------------

--
-- Table structure for table `ocr_logs`
--

CREATE TABLE `ocr_logs` (
  `log_id` int(11) NOT NULL,
  `doc_id` int(11) NOT NULL,
  `raw_text` text NOT NULL,
  `clean_text` text NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ocr_logs`
--

INSERT INTO `ocr_logs` (`log_id`, `doc_id`, `raw_text`, `clean_text`, `created_at`) VALUES
(1, 11, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 17:51:59'),
(2, 12, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 17:53:21'),
(3, 13, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 17:58:26'),
(4, 14, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 18:03:00'),
(5, 15, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 18:07:03'),
(6, 16, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 22:02:53'),
(7, 17, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 22:03:48'),
(8, 18, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 22:07:39'),
(9, 19, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 22:07:59'),
(10, 20, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 22:08:58'),
(11, 21, 'Fake OCR output for Form 1A', 'Fake OCR output for Form 1A', '2026-03-12 22:12:45'),
(12, 22, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:01:01'),
(13, 23, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:02:05'),
(14, 24, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:03:09'),
(15, 25, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:03:41'),
(16, 26, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:06:08'),
(17, 27, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:19:28'),
(18, 28, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:47:21'),
(19, 29, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:48:26'),
(20, 30, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:48:43'),
(21, 31, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:48:56'),
(22, 32, 'Processed via pipeline — Form 1A', 'Processed via pipeline — Form 1A', '2026-03-13 19:49:16');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(45) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(45) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `username`, `password_hash`, `role`) VALUES
(1, 'admin', '123', 'admin'),
(2, 'staff', '123', 'staff');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD PRIMARY KEY (`log_id`);

--
-- Indexes for table `data_fields`
--
ALTER TABLE `data_fields`
  ADD PRIMARY KEY (`field_id`),
  ADD UNIQUE KEY `field_name` (`field_name`);

--
-- Indexes for table `documents`
--
ALTER TABLE `documents`
  ADD PRIMARY KEY (`doc_id`),
  ADD KEY `fk_doc_user` (`user_id`),
  ADD KEY `fk_doc_type` (`type_id`);

--
-- Indexes for table `document_data`
--
ALTER TABLE `document_data`
  ADD PRIMARY KEY (`data_id`),
  ADD KEY `fk_dd_doc` (`doc_id`),
  ADD KEY `fk_dd_field` (`field_id`);

--
-- Indexes for table `document_types`
--
ALTER TABLE `document_types`
  ADD PRIMARY KEY (`type_id`);

--
-- Indexes for table `ocr_logs`
--
ALTER TABLE `ocr_logs`
  ADD PRIMARY KEY (`log_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `activity_logs`
--
ALTER TABLE `activity_logs`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `data_fields`
--
ALTER TABLE `data_fields`
  MODIFY `field_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=235;

--
-- AUTO_INCREMENT for table `documents`
--
ALTER TABLE `documents`
  MODIFY `doc_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- AUTO_INCREMENT for table `document_data`
--
ALTER TABLE `document_data`
  MODIFY `data_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=677;

--
-- AUTO_INCREMENT for table `document_types`
--
ALTER TABLE `document_types`
  MODIFY `type_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `ocr_logs`
--
ALTER TABLE `ocr_logs`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `documents`
--
ALTER TABLE `documents`
  ADD CONSTRAINT `fk_doc_type` FOREIGN KEY (`type_id`) REFERENCES `document_types` (`type_id`),
  ADD CONSTRAINT `fk_doc_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `document_data`
--
ALTER TABLE `document_data`
  ADD CONSTRAINT `fk_dd_doc` FOREIGN KEY (`doc_id`) REFERENCES `documents` (`doc_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_dd_field` FOREIGN KEY (`field_id`) REFERENCES `data_fields` (`field_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
