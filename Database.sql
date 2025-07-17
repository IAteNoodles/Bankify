-- Banking.People definition

CREATE TABLE `People` (
  `ID` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Public Key` varchar(450) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Banking.Staff definition

CREATE TABLE `Staff` (
  `People ID` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Type` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `People_ID` (`People ID`),
  CONSTRAINT `People_ID` FOREIGN KEY (`People ID`) REFERENCES `People` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Banking.`User` definition

CREATE TABLE `User` (
  `People ID` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `User_FK` (`People ID`),
  CONSTRAINT `User_FK` FOREIGN KEY (`People ID`) REFERENCES `People` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Banking.Account_Application definition

CREATE TABLE `Account_Application` (
  `ID` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `User_ID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Account_ID` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Hash` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `CreationTime` datetime NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `Account_Application_FK` (`User_ID`),
  CONSTRAINT `Account_Application_FK` FOREIGN KEY (`User_ID`) REFERENCES `User` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Banking.Accounts definition

CREATE TABLE `Accounts` (
  `User ID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ID` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Balance` decimal(10,0) NOT NULL DEFAULT 0,
  PRIMARY KEY (`ID`),
  KEY `Accounts_FK` (`User ID`),
  CONSTRAINT `Accounts_FK` FOREIGN KEY (`User ID`) REFERENCES `User` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;