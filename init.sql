--Przyznanie wszystkich praw i dodanie urzywkownika

--CREATE USER app WITH ENCRYPTED PASSWORD 'qwerty';
--CREATE USER student WITH ENCRYPTED PASSWORD 'student';
--CREATE DATABASE student;
--GRANT ALL PRIVILEGES ON DATABASE student TO app;
--GRANT ALL PRIVILEGES ON DATABASE student TO student;
--CREATE EXTENSION postgis;

--Usunięcie ewentualnych pozostałości
 drop table if exists "klienci" cascade;
 drop table if exists "odbyte_wycieczki" cascade;
 drop table if exists "rezerwacje" cascade;
 drop table if exists "osrodki" cascade;
 drop table if exists "wycieczki" cascade;

--Tworzenie tablei

CREATE TABLE osrodki(
	id_osrodka INT PRIMARY KEY UNIQUE NOT NULL,
	lokacja GEOGRAPHY NOT NULL,
	opis TEXT
);

CREATE INDEX ON osrodki USING GIST(lokacja);

CREATE TABLE wycieczki(
	id_wycieczki INT PRIMARY KEY UNIQUE NOT NULL,
	punkty_wycieczki INT[] NOT NULL,
	dystans REAL
);

CREATE INDEX wycieczki_inedx on wycieczki (id_wycieczki);

CREATE TABLE klienci(
	id_klienta TEXT PRIMARY KEY UNIQUE NOT NULL,
	kilometry INT,
	ilosc_wycieczek INT
);

CREATE INDEX klienci_inedx on klienci (id_klienta);

CREATE TABLE rezerwacje(
	id_rezerwacji INT PRIMARY KEY UNIQUE NOT NULL,
	data DATE NOT NULL,
	id_klienta TEXT NOT NULL,
	id_osrodka INT NOT NULL
);

CREATE INDEX rezerwacje_inedx on rezerwacje (id_osrodka);

--Tworzenie sekwancji (auto_id)

CREATE SEQUENCE seq_id_rezerwacji
				START WITH 1
				INCREMENT BY 1;

ALTER TABLE rezerwacje 
			ALTER COLUMN id_rezerwacji
			SET DEFAULT nextval('seq_id_rezerwacji');

ALTER SEQUENCE seq_id_rezerwacji OWNED BY
			rezerwacje.id_rezerwacji;

