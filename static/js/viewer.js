let currentRenderer = null;
let currentAnimationId = null;

function initViewer(containerId, blob) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';

    // Cleanup previous renderer and animation
    if (currentRenderer) {
        currentRenderer.dispose();
        if (currentRenderer.domElement && currentRenderer.domElement.parentNode) {
            currentRenderer.domElement.parentNode.removeChild(currentRenderer.domElement);
        }
    }
    if (currentAnimationId) {
        cancelAnimationFrame(currentAnimationId);
    }

    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeeeeee);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    camera.position.set(100, 100, 100);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);
    currentRenderer = renderer;

    const controls = new THREE.OrbitControls(camera, renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);

    const loader = new THREE.STLLoader();
    const url = URL.createObjectURL(blob);

    loader.load(url, function (geometry) {
        const material = new THREE.MeshPhongMaterial({ color: 0x007bff, specular: 0x111111, shininess: 200 });
        const mesh = new THREE.Mesh(geometry, material);

        // Center the model
        geometry.computeBoundingBox();
        const center = new THREE.Vector3();
        geometry.boundingBox.getCenter(center);
        mesh.position.sub(center);

        scene.add(mesh);

        // Adjust camera to fit the model
        const size = new THREE.Vector3();
        geometry.boundingBox.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z);
        camera.position.set(maxDim * 1.5, maxDim * 1.5, maxDim * 1.5);
        camera.lookAt(0, 0, 0);
        controls.update();

        URL.revokeObjectURL(url);
    });

    function animate() {
        currentAnimationId = requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    animate();

    // Resize handling (only for the current renderer)
    const onWindowResize = () => {
        if (currentRenderer !== renderer) {
            window.removeEventListener('resize', onWindowResize);
            return;
        }
        const width = container.clientWidth;
        const height = container.clientHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    };
    window.addEventListener('resize', onWindowResize);
}
