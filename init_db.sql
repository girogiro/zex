-- create db zex owned by user django
create user django with createdb password 'django';
create database zex with owner django encoding 'UTF8' lc_collate 'C' lc_ctype 'C' template template0;

-- set fulltext search in zex database
\c zex;
create extension if not exists unaccent;
create text search configuration usimple (parser='default');
alter text search configuration usimple alter mapping for asciiword, asciihword, hword_asciipart, hword_numpart, word, hword, numword, hword_part with unaccent, simple;
