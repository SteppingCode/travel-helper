create table IF NOT EXISTS inf(
    id INTEGER primary key AUTOINCREMENT,
    id_inf INTEGER not null,
    main_photo TEXT not null,
    description_subtitle text not null,
    gallery_1 text not null,
    name_photo_1 text not null, 
    gallery_2 text not null,
    gallery_3 text not null,
    description1 text not null,
    items_photo_1 text not null,
    items_heading_1 text not null,
    items_description_1 text not null,
    items_photo_2 text not null,
    items_heading_2 text not null,
    items_description_2 text not null,
    items_photo_3 text not null,
    items_heading_3 text not null,
    items_description_3 text not null,
    FOREIGN key(id_inf) REFERENCES places(id)

)