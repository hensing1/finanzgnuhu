CREATE TABLE IF NOT EXISTS "Konten" ("IBAN" 
            CHAR(20) 
             
            NOT NULL
            
            
            , "Name" 
            VARCHAR(50) 
             
            NULL
            
            
            , "Bank" 
            VARCHAR(20) 
             
            NULL
            
            
            , "Typ" 
            VARCHAR(20) 
             
            NULL
            
            
            , PRIMARY KEY ("IBAN"));
CREATE TABLE IF NOT EXISTS "Kategorien" ("ID" 
            INT(10) 
             
            NOT NULL
            
            
            , "Name" 
            VARCHAR(30) 
             
            NOT NULL
            
            
            , PRIMARY KEY ("ID"));
CREATE TABLE IF NOT EXISTS "Umsaetze" ("Hash" 
            CHAR(64) 
             
            NOT NULL
            
            
            , "IBAN" 
            CHAR(20) 
             
            NOT NULL
            
            
            , "Buchung" 
            DATE 
             
            NOT NULL
            
            
            , "Wertstellungsdatum" 
            DATE 
             
            NOT NULL
            
            
            , "Tagesnummer" 
            INT(10) 
             
            NOT NULL
            
            
            , "Sender" 
            TEXT(100) 
             
            NOT NULL
            
            
            , "Empfaenger" 
            TEXT(100) 
             
            NOT NULL
            
            
            , "Buchungstext" 
            TEXT(50) 
             
            NOT NULL
            
            
            , "Verwendungszweck" 
           TEXT(50) 
             
            NULL
            
            
            , "Saldo" 
            INT(10) 
             
            NOT NULL
            
            
            , "Betrag" 
            INT(10) 
             
            NOT NULL
            
            
            , "Einnahme" 
            BOOLEAN 
             
            NOT NULL
            
            
            , "Kategorie" 
            INT(10) 
             
            NOT NULL
            
            DEFAULT 0
            , "ignorieren" 
            BOOLEAN 
             
            NOT NULL
            
            DEFAULT 0
            , PRIMARY KEY ("Hash"), CONSTRAINT "0" FOREIGN KEY ("IBAN") REFERENCES "Konten" ("IBAN") ON UPDATE RESTRICT ON DELETE RESTRICT, CONSTRAINT "1" FOREIGN KEY ("Kategorie") REFERENCES "Kategorien" ("ID") ON UPDATE RESTRICT ON DELETE RESTRICT);
