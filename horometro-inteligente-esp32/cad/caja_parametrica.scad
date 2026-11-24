// Caja para horometro: dimensiones en mm. Abrir con OpenSCAD.
// NO imprimir hasta medir placa, switch y cable USB.
// F6 para renderizar; Archivo > Exportar > STL.
// Exportar base y tapa por separado cambiando pieza.
pieza = "ambas"; // "base", "tapa" o "ambas"
$fn = 64;
largo = 200;
ancho = 120;
alto_total = 55;
pared = 2.4;
fondo = 3;
tapa = 3;
alto_base = alto_total - tapa;

// El agujero se ajusta al diametro REAL de la rosca del switch + holgura.
// 12.3 es SOLO un ejemplo para una rosca medida de 12.0 mm.
diametro_switch = 12.3;
switch_x = 150;
switch_y = 95;

// Pasacable en pared izquierda (X=0), no un encaje exacto al conector de placa.
usb_ancho = 18;
usb_alto = 12;
usb_centro_y = 95;
usb_centro_z = 14;

// Cuatro tornillos autorroscantes 2.9 x 9.5 mm, cabeza exterior.
// Probar el taladro piloto en una muestra; depende del filamento/tornillo.
diametro_piloto = 2.3;
diametro_paso = 3.3;
poste_diametro = 9;
poste_altura = 10;
offset_poste = 8;

function centros() = [
  [offset_poste,offset_poste],
  [largo-offset_poste,offset_poste],
  [offset_poste,ancho-offset_poste],
  [largo-offset_poste,ancho-offset_poste]
];

module base(){
  difference(){
    union(){
      difference(){
        cube([largo,ancho,alto_base]);
        translate([pared,pared,fondo])
          cube([largo-2*pared,ancho-2*pared,alto_base+1]);
      }
      for(p=centros())
        translate([p[0],p[1],alto_base-poste_altura])
          cylinder(h=poste_altura,d=poste_diametro);
      // Nervios verticales: unen los postes altos a las paredes.
      for(p=centros()){
        translate([p[0]-1.2,p[1]<ancho/2 ? pared : p[1],fondo])
          cube([2.4,p[1]<ancho/2 ? p[1]-pared : ancho-pared-p[1],alto_base-fondo]);
        translate([p[0]<largo/2 ? pared : p[0],p[1]-1.2,fondo])
          cube([p[0]<largo/2 ? p[0]-pared : largo-pared-p[0],2.4,alto_base-fondo]);
      }
    }
    for(p=centros())
      translate([p[0],p[1],alto_base-8]) cylinder(h=9,d=diametro_piloto);
    translate([-1,usb_centro_y-usb_ancho/2,usb_centro_z-usb_alto/2])
      cube([pared+2,usb_ancho,usb_alto]);
  }
}

module lid(){
  difference(){
    cube([largo,ancho,tapa]);
    for(p=centros())
      translate([p[0],p[1],-1]) cylinder(h=tapa+2,d=diametro_paso);
    translate([switch_x,switch_y,-1]) cylinder(h=tapa+2,d=diametro_switch);
  }
}

if(pieza=="base")base();
if(pieza=="tapa")lid();
if(pieza=="ambas"){
  base();
  translate([0,ancho+12,0])lid();
}
