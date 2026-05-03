PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Kategorien" ("ID" 
            INT(10) 
             
            NOT NULL
            
            
            , "Name" 
            VARCHAR(30) 
             
            NOT NULL
            
            
            , PRIMARY KEY ("ID"));
INSERT INTO Kategorien VALUES(0,'');
INSERT INTO Kategorien VALUES(1,'Reise');
INSERT INTO Kategorien VALUES(2,'Essen');
INSERT INTO Kategorien VALUES(3,'Sparkonto');
INSERT INTO Kategorien VALUES(4,'Bargeld');
INSERT INTO Kategorien VALUES(5,'Telefon');
INSERT INTO Kategorien VALUES(6,'Auto');
INSERT INTO Kategorien VALUES(7,'Gesundheit');
INSERT INTO Kategorien VALUES(8,'Abos');
INSERT INTO Kategorien VALUES(9,'Anschaffungen');
INSERT INTO Kategorien VALUES(10,'Uni');
INSERT INTO Kategorien VALUES(11,'Freizeit');
INSERT INTO Kategorien VALUES(12,'Geschenke');
COMMIT;
