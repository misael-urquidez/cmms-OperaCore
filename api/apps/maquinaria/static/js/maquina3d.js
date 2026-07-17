let scene;
let camera;
let renderer;
let controls;
let modeloActual = null;
let loader;

// =============================
// INICIALIZAR ESCENA
// =============================
function iniciarEscena(){
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050505);

    // CAMARA
    camera = new THREE.PerspectiveCamera(
        60,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );
    camera.position.set(0, 4, 10);

    // RENDER (Ajustamos para que use el contenedor correcto en lugar de window si es necesario, pero mantenemos tu lógica)
    renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: false
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;

    const contenedor = document.getElementById("modelo3d");
    if (contenedor) {
        contenedor.appendChild(renderer.domElement);
    } else {
        console.warn("No se encontró el contenedor con ID 'modelo3d'. Añadiendo al body...");
        document.body.appendChild(renderer.domElement);
    }

    // CONTROLES
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 3;
    controls.maxDistance = 20;

    // =============================
    // ILUMINACIÓN INDUSTRIAL
    // =============================
    let luzAmbiente = new THREE.HemisphereLight(0xffffff, 0x333333, 2);
    scene.add(luzAmbiente);

    let luzPrincipal = new THREE.DirectionalLight(0xffffff, 3);
    luzPrincipal.position.set(5, 10, 5);
    luzPrincipal.castShadow = true;
    scene.add(luzPrincipal);

    // LUZ AZUL TECNOLÓGICA
    let luzAzul = new THREE.PointLight(0x00ffff, 2, 20);
    luzAzul.position.set(-5, 5, 5);
    scene.add(luzAzul);

    // =============================
    // PISO INDUSTRIAL Y GRID
    // =============================
    let piso = new THREE.Mesh(
        new THREE.PlaneGeometry(30, 30),
        new THREE.MeshStandardMaterial({
            color: 0x111827,
            roughness: .8
        })
    );
    piso.rotation.x = -Math.PI / 2;
    scene.add(piso);

    let grid = new THREE.GridHelper(30, 30, 0x00ffff, 0x333333);
    scene.add(grid);

    // CARGADOR GLB
    loader = new THREE.GLTFLoader();
}

// =============================
// CARGAR MODELO 3D
// =============================
function cargarModelo(url){
    if(!url) return;

    // Eliminar modelo anterior
    if(modeloActual){
        scene.remove(modeloActual);
        modeloActual = null;
    }

    // RESOLVER RUTA DINÁMICA: 
    // Si la base de datos devuelve 'images/conveyor.glb', lo direccionamos a /static/images/...
    // Si usas la carpeta media, cambia "/static/" por "/media/"
    let rutaCompleta = url.startsWith('/') ? url : "/static/" + url;

    console.log("Intentando cargar modelo desde:", rutaCompleta);

    // Cargar nuevo modelo
    loader.load(
        rutaCompleta,
        function(gltf){
            modeloActual = gltf.scene;

            // Tamaño automático y centrado básico
            modeloActual.scale.set(2, 2, 2);
            modeloActual.position.set(0, 0, 0);

            // Sombras
            modeloActual.traverse(function(obj){
                if(obj.isMesh){
                    obj.castShadow = true;
                    obj.receiveShadow = true;
                }
            });

            scene.add(modeloActual);

            // Centrar la cámara al objeto cargado
            const box = new THREE.Box3().setFromObject(modeloActual);
            const center = box.getCenter(new THREE.Vector3());
            controls.target.copy(center);
        },
        undefined,
        function(error){
            console.error("Error cargando modelo 3D en la ruta: " + rutaCompleta, error);
        }
    );
}

// =============================
// CARGAR MAQUINAS DESDE DJANGO (CORREGIDO)
// =============================
function cargarMaquinas(){
    fetch("/maquinaria/api/v1/list/")
    .then(response => response.json())
    .then(data => {
        let lista = document.getElementById("listaMaquinas");
        if(!lista) return;
        
        lista.innerHTML = "";

        data.forEach(maquina => {
            let card = document.createElement("div");
            card.className = "maquina";
            card.innerHTML = `
                <h3>${maquina.nombre}</h3>
                <p>Código: ${maquina.codigo}</p>
                <p>Marca: ${maquina.marca}</p>
                <p>Modelo: ${maquina.modelo}</p>
            `;

            card.onclick = function(){
                document.getElementById("nombre").innerHTML = maquina.nombre;
                document.getElementById("modelo").innerHTML = maquina.modelo;
                
                // Aseguramos capturar si viene un objeto de estado o un string directo
                let estadoElement = document.getElementById("estado");
                if (estadoElement) {
                    estadoElement.innerHTML = maquina.estado_maquina?.nombre || maquina.estado_maquina || "N/A";
                }

                if(maquina.modelo_3d){
                    cargarModelo(maquina.modelo_3d);
                }
            };

            lista.appendChild(card);
        });
    }) // Se removió la llave y paréntesis extra que rompía el código aquí
    .catch(error => {
        console.error("Error API:", error);
    });
}

// =============================
// ANIMACIÓN
// =============================
function animate(){
    requestAnimationFrame(animate);
    controls.update();

    if(modeloActual){
        modeloActual.rotation.y += 0.002;
    }

    renderer.render(scene, camera);
}

// =============================
// RESPONSIVE
// =============================
window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// =============================
// INICIO
// =============================
iniciarEscena();
cargarMaquinas();
animate();