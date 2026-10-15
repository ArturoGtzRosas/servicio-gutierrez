BEGIN TRANSACTION;
CREATE TABLE cotizaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    servicio TEXT,
                    modelo TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
INSERT INTO "cotizaciones" VALUES(1,'Juan P','bateria','Hp G5','2026-02-13 19:14:00');
CREATE TABLE mensajes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, email TEXT, telefono TEXT, mensaje TEXT, leido INTEGER DEFAULT 0, asunto TEXT);
INSERT INTO "mensajes" VALUES(1,'15/10/2026 13:53','Roberto López','robertol@gmail.com','','Equipo no enciende',0,'Otro');
INSERT INTO "mensajes" VALUES(2,'15/10/2026 13:55','Hugo Gutiérrez','hugogtzrosas@gmail.com','','Mi equipo esta lento',0,'Mantenimiento');
INSERT INTO "mensajes" VALUES(3,'15/10/2026 14:07','Ernesto Sánchez','neto@gmail.com','','Necesito aumento de memoria y cambio de disco duro.',0,'Actualizacion');
CREATE TABLE notas_venta 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, 
                     direccion TEXT, telefono TEXT, equipo TEXT, servicio TEXT, total REAL, observaciones TEXT);
INSERT INTO "notas_venta" VALUES(1,'15/10/2026 12:47','Supervisión Escolar J212','Emiliano Zapata s/n, Santa María Nativitas, Chimalhuacán, Estado de México.','55 3013 1070','Laptop Lanix','Office 2024 Professional Plus',650.0,'Sin Paqueteria');
INSERT INTO "notas_venta" VALUES(2,'15/10/2026 13:08','J.N Unidos Avanzamos','Chimalhuacan','55 2523 8965','Laptop Hp 240 G5','(x2) Office Professional Plus 2024',1300.0,'Sin office');
INSERT INTO "notas_venta" VALUES(3,'15/10/2026 13:13','Maestra Monse','Chicoloapan','55 1234 5678','Laptop Asus','(x3) Office Professional Plus 2024',1950.0,'Sin office');
CREATE TABLE presupuestos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, 
                       telefono TEXT, equipo TEXT, servicios TEXT, total REAL);
INSERT INTO "presupuestos" VALUES(3,'09/10/2026 10:53','Jardín de niños "Unidos Avanzamos"','55 2324 7898','Sistema de Video Vigilancia','(x1) DVR con conexión a Internet, (x8) Cámara para exteriores',8800.0);
INSERT INTO "presupuestos" VALUES(4,'09/10/2026 11:59','Arturo Gtz','55 4031 3150','Laptop Asus','(x1) Memoria RAM DDR4 8 GB',2200.0);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('usuarios',1);
INSERT INTO "sqlite_sequence" VALUES('cotizaciones',1);
INSERT INTO "sqlite_sequence" VALUES('presupuestos',4);
INSERT INTO "sqlite_sequence" VALUES('notas_venta',3);
INSERT INTO "sqlite_sequence" VALUES('mensajes',3);
CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    email TEXT UNIQUE,
                    password TEXT);
INSERT INTO "usuarios" VALUES(1,'Arturo','arturo@servicio.com','1234');
COMMIT;