<script setup lang="ts">
import FretboardExercise from './features/fretboard/FretboardExercise.vue'
</script>

<template>
  <main>
    <h1>Guitar Exercises</h1>
    <FretboardExercise />
  </main>
</template>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: system-ui, sans-serif;
  background: #f5f5f5;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 3rem 1rem;
}

main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  max-width: 600px;
  width: 100%;
}

h1 {
  font-size: 2rem;
  color: #333;
}
</style>
