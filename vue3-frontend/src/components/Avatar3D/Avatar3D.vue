<template>
  <div class="avatar-3d-container">
    <div ref="containerRef" class="w-full h-full"></div>
    <div class="absolute bottom-4 left-0 right-0 flex justify-center">
      <div class="text-xl font-bold text-primary">AI 小助手</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { useChatStore } from '../../stores/chat'

const containerRef = ref(null)
const chatStore = useChatStore()

let scene = null
let camera = null
let renderer = null
let controls = null
let avatar = null
let mixer = null
let clock = null

// 创建3D场景
function initScene() {
  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf8f0f0)

  // 创建相机
  camera = new THREE.PerspectiveCamera(75, containerRef.value.clientWidth / containerRef.value.clientHeight, 0.1, 1000)
  camera.position.z = 5

  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(containerRef.value.clientWidth, containerRef.value.clientHeight)
  containerRef.value.appendChild(renderer.domElement)

  // 添加控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.enableZoom = false
  controls.enablePan = false

  // 添加灯光
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(1, 1, 1)
  scene.add(directionalLight)

  // 创建卡通人物
  createAvatar()

  // 初始化时钟
  clock = new THREE.Clock()

  // 开始动画循环
  animate()
}

// 创建卡通人物
function createAvatar() {
  // 创建头部
  const headGeometry = new THREE.SphereGeometry(1, 32, 32)
  const headMaterial = new THREE.MeshPhongMaterial({ color: 0xffddcc })
  const head = new THREE.Mesh(headGeometry, headMaterial)
  scene.add(head)

  // 创建眼睛
  const eyeGeometry = new THREE.SphereGeometry(0.15, 16, 16)
  const eyeMaterial = new THREE.MeshPhongMaterial({ color: 0x000000 })

  const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial)
  leftEye.position.set(-0.3, 0.3, 0.8)
  head.add(leftEye)

  const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial)
  rightEye.position.set(0.3, 0.3, 0.8)
  head.add(rightEye)

  // 创建嘴巴
  const mouthGeometry = new THREE.CylinderGeometry(0.2, 0.2, 0.05, 16)
  const mouthMaterial = new THREE.MeshPhongMaterial({ color: 0xff6666 })
  const mouth = new THREE.Mesh(mouthGeometry, mouthMaterial)
  mouth.position.set(0, -0.2, 0.9)
  mouth.rotation.x = Math.PI / 2
  head.add(mouth)

  // 创建身体
  const bodyGeometry = new THREE.CylinderGeometry(0.6, 0.8, 1.5, 32)
  const bodyMaterial = new THREE.MeshPhongMaterial({ color: 0xff8888 })
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
  body.position.set(0, -1.5, 0)
  scene.add(body)

  // 创建手臂
  const armGeometry = new THREE.CylinderGeometry(0.2, 0.2, 1, 16)
  const armMaterial = new THREE.MeshPhongMaterial({ color: 0xffddcc })

  const leftArm = new THREE.Mesh(armGeometry, armMaterial)
  leftArm.position.set(-0.8, -1, 0)
  leftArm.rotation.z = Math.PI / 6
  scene.add(leftArm)

  const rightArm = new THREE.Mesh(armGeometry, armMaterial)
  rightArm.position.set(0.8, -1, 0)
  rightArm.rotation.z = -Math.PI / 6
  scene.add(rightArm)

  avatar = head
}

// 动画循环
function animate() {
  requestAnimationFrame(animate)

  const delta = clock.getDelta()

  if (mixer) {
    mixer.update(delta)
  }

  // 根据聊天状态更新表情
  updateAvatarExpression()

  controls.update()
  renderer.render(scene, camera)
}

// 更新头像表情
function updateAvatarExpression() {
  if (!avatar) return

  switch (chatStore.status) {
    case 'recording':
      // 录音状态 - 说话表情
      animateMouth(true)
      break
    case 'playing':
      // 播放状态 - 说话表情
      animateMouth(true)
      break
    case 'thinking':
      // 思考状态 - 思考表情
      animateMouth(false)
      break
    default:
      // 默认状态 - 微笑表情
      animateMouth(false)
      break
  }
}

// 动画嘴巴
function animateMouth(isSpeaking) {
  if (!avatar) return

  const mouth = avatar.children.find(child => child.position.y === -0.2 && child.position.z === 0.9)
  if (mouth) {
    if (isSpeaking) {
      // 说话动画
      mouth.scale.y = 1.5 + Math.sin(Date.now() * 0.01) * 0.5
    } else {
      // 微笑状态
      mouth.scale.y = 1
    }
  }
}

// 响应窗口大小变化
function handleResize() {
  if (!camera || !renderer || !containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

// 监听状态变化
watch(() => chatStore.status, (newStatus) => {
  updateAvatarExpression()
})

// 组件挂载时初始化
onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  
  if (renderer) {
    containerRef.value.removeChild(renderer.domElement)
    renderer.dispose()
  }
  
  if (controls) {
    controls.dispose()
  }
  
  if (scene) {
    scene.traverse((object) => {
      if (object.geometry) object.geometry.dispose()
      if (object.material) {
        if (Array.isArray(object.material)) {
          object.material.forEach(material => material.dispose())
        } else {
          object.material.dispose()
        }
      }
    })
  }
})
</script>

<style scoped>
.avatar-3d-container {
  position: relative;
  width: 100%;
  height: 300px;
  border-radius: 20px;
  overflow: hidden;
  background: linear-gradient(135deg, #fff5f5 0%, #ffe4e4 100%);
  box-shadow: 0 10px 30px rgba(255, 182, 193, 0.3);
}

@media (max-width: 768px) {
  .avatar-3d-container {
    height: 200px;
  }
}
</style>