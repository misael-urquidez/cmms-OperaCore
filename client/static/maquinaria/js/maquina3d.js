import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export function initMaquinaViewer(modelPath, staticUrl) {
    const container = document.getElementById('canvas-container');

    if (container && modelPath && modelPath !== "None" && modelPath.trim() !== "") {
        // 1. Escena, Cámara y Renderizador
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);

        // 2. Controles de órbita
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;

        // 3. Iluminación
        const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 2);
        directionalLight.position.set(5, 10, 7);
        scene.add(directionalLight);

        // 4. Carga del archivo .glb (soporta tanto URLs locales blob: como rutas estáticas del servidor)
        const loader = new GLTFLoader();
        let fullUrl = modelPath;
        
        // Si no es una URL local de blob, concatenamos la ruta estática
        if (!modelPath.startsWith('blob:')) {
            fullUrl = staticUrl + 'images/' + modelPath;
        }

        loader.load(fullUrl, function (gltf) {
            const model = gltf.scene;
            
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());

            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 3.5 / maxDim;
            model.scale.set(scale, scale, scale);

            model.position.sub(center.multiplyScalar(scale));
            scene.add(model);

            camera.position.set(0, 2, 5);
            controls.update();

        }, undefined, function (error) {
            console.error("Error al cargar el modelo 3D:", error);
        });

        // 5. Animación continua
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        animate();  

        // Responsividad
        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });
    }
}