.. _copydbdata:

=========================
How to copy database data
=========================

**Intro**

Årsagen til at dette overhovedet er relevant og nødvendigt skyldes introduktionen af nye typer af scannere. Den nyeste udgave af webscanneren kan nu også filscanne.
Derfor er database designet ændret så meget at det er umuligt at tilføje skema ændringer uden at dumpe data først og derefter loade det ind igen.

De tabeller som har ændret sig er domains, scanner og scan tabellerne.

Da data fra scanningerne er her og nu data er det nemmeste at oprette en ny database og overføre brugere og organisationer.

**How to**

Overførsel af data fra en gammel webscanner database til en ny:
Når du skal overføre data fra en gammel udgave af webscanner databasen til en ny skal du gøre følgende:

Start med at ændre navnet på den tabel du vil overføre data til fra psql commandline:

.. code:: console

    $ ALTER TABLE os2webscanner_userprofile RENAME TO os2webscanner_userprofile_new;

Følgende kommando dumper tabellen "os2webscanner_userprofile" fra den gamle db "os2webscanner" og opretter den med data i den nye database "os2datascanner". Kør ikke kommandoen fra psql:

.. code:: console

    $ pg_dump -U postgres -t os2webscanner_userprofile os2webscanner | psql -U postgres -d os2datascanner

Gå tilbage til psql kommandolinjen, og kør følgende kommando for at give din database bruger ejerskab af den ny oprettede tabel:

.. code:: console

    $ ALTER TABLE os2webscanner_userprofile OWNER TO os2datascanner;

Nu kan du overføre dataen fra den overførte tabel til den eksisterende:

.. code:: console

    $ INSERT INTO os2webscanner_userprofile_new (id, is_group_admin, is_upload_only, organization_id, user_id) SELECT * FROM os2webscanner_userprofile;
