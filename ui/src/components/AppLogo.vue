<template>
  <div class="logo-container" @click="$router.push('/')">
    <div class="logo-wrapper">
      <div class="glow-effect"></div>

      <div class="img-container" :class="[compact ? 'compact' : 'full']">
        <img :src="compact ? '/brand/icon.png' : '/brand/logo.png'" alt="IPLoom" class="logo-img" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  compact: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'md'
  }
})
</script>

<style scoped>
.logo-container {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.logo-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.glow-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(37, 99, 235, 0.05);
  border-radius: 9999px;
  filter: blur(24px);
  opacity: 0;
  transition: opacity 0.3s;
}

.logo-container:hover .glow-effect {
  opacity: 1;
}

.img-container {
  position: relative;
  z-index: 10;
  transition: all 0.5s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-container:hover .img-container {
  transform: scale(1.1);
}

.img-container.compact {
  width: 40px;
  height: 40px;
  overflow: hidden;
}

.img-container.full {
  height: 128px;
  width: auto;
  margin-top: 10px;
  margin-left: 0px;
}

.logo-img {
  height: 100%;
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 2px 8px rgba(30, 64, 175, 0.3));
}

.dark .logo-img {
  filter: drop-shadow(0 2px 8px rgba(255, 255, 255, 0.1));
}
</style>
