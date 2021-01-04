CREATE DATABASE IF NOT EXISTS mdt_tracker;
USE mdt_tracker;

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `master`
--

DROP TABLE IF EXISTS `master`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `master` (
  `id` int(11) NOT NULL COMMENT 'Numerical ID for experiment',
  `owner` varchar(50) DEFAULT NULL,
  `userName` varchar(30) DEFAULT '' COMMENT 'Username of experiment owner',
  `modelType` varchar(30) NOT NULL DEFAULT 'CM4' COMMENT 'Type of model',
  `displayName` varchar(100) DEFAULT NULL COMMENT 'Alternate name to display for experiment',
  `expName` varchar(100) DEFAULT NULL COMMENT 'Experiment name',
  `expLength` int(5) DEFAULT NULL COMMENT 'Experiment length (in years)',
  `expYear` int(5) DEFAULT NULL COMMENT 'Most recent year in history directory at GFDL',
  `expType` varchar(30) DEFAULT NULL COMMENT 'Experiment type',
  `expMIP` varchar(100) DEFAULT NULL COMMENT 'CMIP MIP associated with this experiment',
  `expLabels` varchar(500) DEFAULT NULL COMMENT 'Comma separated list of keywords',
  `urlCurator` varchar(100) DEFAULT NULL COMMENT 'Curator exper_id',
  `pathPP` varchar(200) DEFAULT NULL COMMENT 'Path to post-processing directory',
  `pathAnalysis` varchar(200) DEFAULT NULL COMMENT 'Path to analysis directory',
  `pathDB` varchar(200) DEFAULT NULL COMMENT 'Path to global sums database directory',
  `pathScript` varchar(200) DEFAULT NULL COMMENT 'Path to experiment runscript',
  `pathXML` varchar(200) DEFAULT NULL COMMENT 'Path to experiment XML',
  `pathLog` varchar(200) DEFAULT NULL COMMENT 'Path to experiment log file',
  `status` varchar(30) DEFAULT NULL COMMENT 'Status of job (Running or Complete)',
  `jobID` varchar(30) DEFAULT NULL COMMENT 'Batch job ID',
  `queue` varchar(30) DEFAULT NULL COMMENT 'Priority queue of job',
  `gfdlHistoryYear` varchar(30) DEFAULT NULL COMMENT 'Latest history file on GFDL /archive',
  `refresh` int(1) DEFAULT NULL COMMENT 'Refresh experiment (0=False, 1=True)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  FULLTEXT KEY `expLabels` (`expLabels`),
  FULLTEXT KEY `userName` (`userName`),
  FULLTEXT KEY `modelType` (`modelType`),
  FULLTEXT KEY `displayName` (`displayName`),
  FULLTEXT KEY `expName` (`expName`),
  FULLTEXT KEY `queue` (`queue`),
  FULLTEXT KEY `status` (`status`),
  FULLTEXT KEY `modelType_2` (`modelType`),
  FULLTEXT KEY `search_text` (`expLabels`,`userName`,`modelType`,`displayName`,`expName`,`queue`,`status`),
  FULLTEXT KEY `expMIP` (`expMIP`),
  FULLTEXT KEY `expLabels_2` (`expLabels`),
  FULLTEXT KEY `expMIP_2` (`expMIP`),
  FULLTEXT KEY `userName_2` (`userName`),
  FULLTEXT KEY `modelType_3` (`modelType`),
  FULLTEXT KEY `displayName_2` (`displayName`),
  FULLTEXT KEY `expName_2` (`expName`),
  FULLTEXT KEY `queue_2` (`queue`),
  FULLTEXT KEY `status_2` (`status`),
  FULLTEXT KEY `expLabels_3` (`expLabels`,`expMIP`,`userName`,`modelType`,`displayName`,`expName`,`queue`,`status`),
  FULLTEXT KEY `expLabels_4` (`expLabels`,`expType`,`userName`,`modelType`,`displayName`,`expName`,`queue`,`status`,`expMIP`),
  FULLTEXT KEY `search_index2` (`expLabels`,`expType`,`userName`,`modelType`,`displayName`,`expName`,`queue`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `master`
--

LOCK TABLES `master` WRITE;
/*!40000 ALTER TABLE `master` DISABLE KEYS */;
/*!40000 ALTER TABLE `master` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `parameters`
--

DROP TABLE IF EXISTS `parameters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `parameters` (
  `hexkey` varchar(100) NOT NULL,
  `expID` varchar(100) DEFAULT NULL,
  `param` varchar(255) DEFAULT NULL,
  `val` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`hexkey`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parameters`
--

LOCK TABLES `parameters` WRITE;
/*!40000 ALTER TABLE `parameters` DISABLE KEYS */;
/*!40000 ALTER TABLE `parameters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_map`
--

DROP TABLE IF EXISTS `project_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_map` (
  `primary_key` varchar(32) NOT NULL COMMENT 'Unique primary key',
  `project_id` int(11) NOT NULL COMMENT 'Project ID',
  `experiment_id` int(11) NOT NULL COMMENT 'Numerical ID specific to the project',
  `master_id` int(11) NOT NULL COMMENT 'Experiment ID from the master table ',
  PRIMARY KEY (`primary_key`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_map`
--

LOCK TABLES `project_map` WRITE;
/*!40000 ALTER TABLE `project_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `project_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `projects` (
  `project_id` int(5) NOT NULL AUTO_INCREMENT COMMENT 'Integer project number used for internal reference',
  `project_name` varchar(50) NOT NULL COMMENT 'Project name, used in URLs and for reference',
  `project_remap` int(11) NOT NULL DEFAULT '0' COMMENT 'Project has unique numbering scheme; 1 = True; 0 = False',
  `project_description` varchar(500) DEFAULT NULL COMMENT 'Project description',
  `project_config` varchar(500) DEFAULT NULL COMMENT 'Project configuration',
  PRIMARY KEY (`project_id`),
  UNIQUE KEY `project_id` (`project_id`),
  UNIQUE KEY `project_name` (`project_name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `projects`
--

LOCK TABLES `projects` WRITE;
/*!40000 ALTER TABLE `projects` DISABLE KEYS */;
/*!40000 ALTER TABLE `projects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sessions`
--

DROP TABLE IF EXISTS `sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sessions` (
  `uid` int(6) NOT NULL,
  `session_id` varchar(36) NOT NULL,
  `remote_addr` varchar(40) DEFAULT NULL,
  `creation_date` datetime DEFAULT NULL,
  `expiration_date` datetime DEFAULT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sessions`
--

LOCK TABLES `sessions` WRITE;
/*!40000 ALTER TABLE `sessions` DISABLE KEYS */;
/*!40000 ALTER TABLE `sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` varchar(100) DEFAULT NULL COMMENT 'OpenID Remote User',
  `name` varchar(100) DEFAULT NULL COMMENT 'Full name',
  `email` varchar(100) NOT NULL COMMENT 'Email address',
  `profile_pic` varchar(100) NOT NULL COMMENT 'Profile picture',
  `remote_addr` varchar(40) DEFAULT NULL,
  `login_date` datetime DEFAULT NULL,
  `perm_view` varchar(150) DEFAULT NULL COMMENT 'CSV list of project IDs that user can view entries',
  `perm_add` varchar(150) DEFAULT '1' COMMENT 'CSV list of project IDs that user can add entries',
  `perm_modify` varchar(150) DEFAULT NULL COMMENT 'CSV list of project IDs that user can modify entries',
  `perm_del` varchar(150) DEFAULT NULL COMMENT 'CSV list of project IDs that user can delete entries',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-12-30 12:00:04
