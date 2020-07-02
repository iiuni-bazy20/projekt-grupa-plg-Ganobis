# -*- coding: utf-8 -*-
#importowanie bibliotek
import codecs
import psycopg2
import sys
import math
from heapq import nsmallest
import json

#funkcja dodające nowe oścordki
def node(numer, szerokosc, dlugosc, opis):
    komenda = "INSERT INTO osrodki(id_osrodka, lokacja, opis) VALUES (" + str(numer) + ",  'SRID=4326;POINT(" + str(dlugosc) + " " + str(szerokosc) + ")', '" + opis + "');"
    kursor.execute(komenda)
    polaczenie.commit()
    print("{\"status\": \"OK\"}")

#dodaje do tableli wycieczki nową wycieczke
def catalog(numer, lista_punktow):
    punkt_jeden = ""
    dystans = 0
    for x in lista_punktow:         #for odpowiedzialny za obliczneie dystansu
        if punkt_jeden == "":
            punkt_jeden = x
        else:
            punkt_dwa = punkt_jeden
            punkt_jeden = x
            komenda = "SELECT ST_Distance((SELECT lokacja FROM osrodki WHERE id_osrodka=" + str(punkt_jeden) + "), (SELECT lokacja FROM osrodki WHERE id_osrodka=" + str(punkt_dwa) + "), true);"       #pobranie dystansu 2 sąsiadujących punktów
            kursor.execute(komenda)
            dyst = kursor.fetchall()
            dystans += dyst[0][0]
    #dodanie do tabeli
    komenda = "INSERT INTO wycieczki(id_wycieczki, punkty_wycieczki, dystans) VALUES (" + str(numer) + ", ARRAY["
    for x in range(len(lista_punktow)):
        if x == len(lista_punktow) - 1:
            komenda += str(lista_punktow[x])
        else:
            komenda += str(lista_punktow[x]) + ", "
    komenda += "], " + str(round(dystans)) + ");"
    kursor.execute(komenda)
    polaczenie.commit()
    print("{\"status\": \"OK\"}")

#funkcja wywolywana po zarezerwowaniu wycieczki przez rowerzyste
def trip(rowerzysta, dzien, wycieczka):
    #dodanie klienta
    komenda = "INSERT INTO klienci(id_klienta, kilometry, ilosc_wycieczek) VALUES ('"+ rowerzysta + "', 0, 0) ON CONFLICT(id_klienta) DO NOTHING;"
    kursor.execute(komenda)
    komenda = "SELECT dystans FROM wycieczki WHERE id_wycieczki=" + str(wycieczka) + ";"
    kursor.execute(komenda)
    dystans = kursor.fetchall()
    #aktualizacja klienta
    komenda = "UPDATE klienci SET kilometry = kilometry + " + str(dystans[0][0]) + ", ilosc_wycieczek = ilosc_wycieczek + 1 WHERE id_klienta = '" + rowerzysta + "';"
    kursor.execute(komenda)
    komenda = "SELECT punkty_wycieczki FROM wycieczki WHERE id_wycieczki = " + str(wycieczka) + ";"
    kursor.execute(komenda)
    tablica_punktow = kursor.fetchall()
    licznik = 0
    #dodanie do tabeli z noclegami planowanych noclegow
    for punkt in tablica_punktow[0][0]:
        komenda = "INSERT INTO rezerwacje(data, id_klienta, id_osrodka) VALUES ((SELECT date '" + dzien + "' + integer '" + str(licznik) + "'), '" + rowerzysta + "', " + str(punkt) + ");"
        licznik += 1
        kursor.execute(komenda)
    polaczenie.commit()
    print("{\"status\": \"OK\"}")

#funkcja zwracająca 3 lub mniej najbliższe punkty noclegowe
def closest_nodes(szerokosc, dlugosc):
    #pobranie osrodkow
    komenda = "SELECT id_osrodka, lokacja, ST_X(lokacja::geometry) AS punkty_x, ST_Y(lokacja::geometry) AS punkty_y FROM osrodki;"
    kursor.execute(komenda)
    osrodki_tab = kursor.fetchall()
    odlegosc_od_osrodka = []
    #dodanie do tablei wszystkkich odlegośći
    for osrodek in osrodki_tab:
        komenda = "SELECT ST_Distance('SRID=4326;POINT(" + str(dlugosc) + " " + str(szerokosc) + ")'::geography, '" + str(osrodek[1]) + "' , true);"
        kursor.execute(komenda)
        odleglosc = kursor.fetchall()
        odlegosc_od_osrodka.append(odleglosc[0][0])
    #wybranie 3 najniejszych odległości
    najmniejsze_odleglosci = nsmallest(3, odlegosc_od_osrodka)
    print("{\"status\": \"OK\", \"data\": [ ")
    for i in range(len(odlegosc_od_osrodka)):
        if najmniejsze_odleglosci[len(najmniejsze_odleglosci)-1] >= odlegosc_od_osrodka[i]:
            print("{\"node\" : " + str(osrodki_tab[i][0]) + ", \"olat\": " + str(osrodki_tab[i][2]) + ", \"olon\": " + str(osrodki_tab[i][3]) + " \"distance\": " + str(round(odlegosc_od_osrodka[i]))) + "}"
    print("]}")

#funkcja zwraca wszystkich gośći w dany ośrodku wybranego dnia
def guests(osrodek, data):
    komenda = "SELECT id_klienta FROM rezerwacje AS r WHERE r.data = '" + data + "' AND r.id_osrodka = " + str(osrodek) + " ORDER BY id_klienta DESC;"
    kursor.execute(komenda)
    rowerzysci = kursor.fetchall()
    print("{\"status\": \"OK\", \"data\": [")
    for rowerzysta in rowerzysci[0]:
        if rowerzysta == rowerzysci[-1]:
            print("{\"cyclist\": \"" + rowerzysta + "\"}")
        else:
            print("{\"cyclist\": \"" + rowerzysta + "\"},")
    print("]}")

#zwraca ranking rowerzystów
def cyclists(limit):
    komenda = "SELECT id_klienta, ilosc_wycieczek AS ilosc, kilometry AS dystans FROM klienci ORDER BY ilosc LIMIT " + str(limit) + ";"
    kursor.execute(komenda)
    ranking = kursor.fetchall()
    print("{\"status\": \"OK\", \"data\": [")
    for rekord in ranking:
        if rekord == ranking[-1]:
            print("{\"cyclist\": \"" + str(rekord[0]) + "\", \"no_trips\": " + str(rekord[1]) + ", \"distance\":" + str(rekord[2]) + "}")
        else:
            print("{\"cyclist\": \"" + str(rekord[0]) + "\", \"no_trips\": " + str(rekord[1]) + ", \"distance\":" + str(rekord[2]) + "},")
    print("}]")

#funkcja party zwraca wszystkich rowerzystów w promieniu 20 km od podanrgo rowrzysty
def party(icyclist, date):
    #wybranie ośrodka w którym przebywa rowerzysta
    komenda = "SELECT id_osrodka FROM rezerwacje WHERE id_klienta = '" + icyclist + "' AND data = '" + date + "';"
    kursor.execute(komenda)
    osrodek = kursor.fetchall()
    #ściągniecie lokalizacji wybranego ośrodka
    komenda = "SELECT lokacja FROM osrodki WHERE id_osrodka = " + str(osrodek[0][0]) + ";"
    kursor.execute(komenda)
    lokalizacja = kursor.fetchall()
    #wybranie poszczególnych rowerzystów
    komenda = "SELECT id_klienta, id_osrodka, ST_DISTANCE('" + lokalizacja[0][0] + "', foo.lokacja, true) AS dystans FROM (SELECT id_klienta, data, o.id_osrodka, o.lokacja FROM rezerwacje JOIN osrodki AS o ON o.id_osrodka = rezerwacje.id_osrodka) AS foo WHERE ST_DISTANCE('" + lokalizacja[0][0] + "', foo.lokacja, true) < 20000 AND foo.id_osrodka =" + str(osrodek[0][0]) + " AND foo.data = '" + date + "' AND id_klienta != '" + icyclist + "';"
    kursor.execute(komenda)
    wyniki = kursor.fetchall()
    print("{\"status\": \"OK\", \"data\": [")
    for rekord in wyniki:
        if rekord == wyniki[-1]:
            print("{\"cyclist\": \"" + str(rekord[0]) + "\", \"node\": " + str(rekord[1]) + ", \"distance\":" + str(rekord[2]) + "}")
        else:
            print("{\"cyclist\": \"" + str(rekord[0]) + "\", \"node\": " + str(rekord[1]) + ", \"distance\":" + str(rekord[2]) + "},")
    print("}]")

try:
    polaczenie_dane = "host='localhost' dbname='student' user='app' password='qwerty'"
    print "Łączenie z baza danych"
    polaczenie = psycopg2.connect(polaczenie_dane)
    kursor = polaczenie.cursor()
    dol = 1
    #jeśli mamy init to uruchom plik sql
    if sys.argv[1] == "--init":
        kursor.execute(open("init.sql", "r").read())
        polaczenie.commit()
        dol += 1
    #czytanie z wszystkich dołączonych do programu plików json
    for licznik in range(dol, len(sys.argv)):
        for linia in open(sys.argv[licznik], "r"):
            #print(linia)
            polecenie = json.loads(linia)
            if polecenie["function"] == "node":
                node(polecenie["body"]["node"],polecenie["body"]["lat"], polecenie["body"]["lon"], polecenie["body"]["description"])
            elif polecenie["function"] == "catalog":
                catalog(polecenie["body"]["version"],polecenie["body"]["nodes"])
            elif polecenie["function"] == "trip":
                trip(polecenie["body"]["cyclist"],polecenie["body"]["date"], polecenie["body"]["version"])
            elif polecenie["function"] == "closest_nodes":
                closest_nodes(polecenie["body"]["ilat"], polecenie["body"]["ilon"])
            elif polecenie["function"] == "guests":
                guests(polecenie["body"]["node"],polecenie["body"]["date"])
            elif polecenie["function"] == "cyclists":
                cyclists(polecenie["body"]["limit"])
            elif polecenie["function"] == "party":
                party(polecenie["body"]["icyclist"], polecenie["body"]["date"])
            else:
                print("Błędna komenda")
    kursor.close()
    polaczenie.close()
    print("Zamknięcie połączenia")
except (Exception, psycopg2.DatabaseError) as error:
    print(error)
finally:
    if polaczenie is not None:
        polaczenie.close()