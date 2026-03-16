<script setup lang="ts">
import { ref, watch } from 'vue'
import { useFretboardExercise } from './useFretboardExercise'

const { currentString, currentFret, streak, lastResult, correctNote, submitAnswer, nextQuestion } =
  useFretboardExercise()

const input = ref('')

function handleSubmit(): void {
  if (!input.value.trim() || lastResult.value !== null) return
  submitAnswer(input.value)
  input.value = ''
}

watch(lastResult, (result, _prev, onCleanup) => {
  if (result !== null) {
    const timeoutId = setTimeout(() => nextQuestion(), 1500)
    onCleanup(() => {
      clearTimeout(timeoutId)
    })
  }
})
</script>

<template>
  <div class="exercise">
    <div class="question">
      String <strong>{{ currentString }}</strong
      >, Fret <strong>{{ currentFret }}</strong>
    </div>

    <div v-if="streak > 0" class="streak">Streak: {{ streak }}</div>

    <form class="answer-form" @submit.prevent="handleSubmit">
      <label for="answer-input">Answer note</label>
      <input
        id="answer-input"
        v-model="input"
        type="text"
        placeholder="Note (e.g. A, C#)"
        :disabled="lastResult !== null"
        autocomplete="off"
        autofocus
      />
      <button type="submit" :disabled="lastResult !== null">Submit</button>
    </form>

    <div v-if="lastResult === 'correct'" class="feedback correct">Correct!</div>
    <div v-else-if="lastResult === 'wrong'" class="feedback wrong">
      Wrong — it was {{ correctNote }}
    </div>
  </div>
</template>

<style scoped>
.exercise {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 2rem;
}

.question {
  font-size: 2rem;
  color: #222;
}

.streak {
  font-size: 1rem;
  color: #666;
}

.answer-form {
  display: flex;
  gap: 0.5rem;
}

.answer-form input {
  padding: 0.5rem 1rem;
  font-size: 1.2rem;
  border: 2px solid #ccc;
  border-radius: 4px;
  width: 10rem;
}

.answer-form input:focus {
  outline: none;
  border-color: #4a90d9;
}

.answer-form button {
  padding: 0.5rem 1.25rem;
  font-size: 1.2rem;
  background: #4a90d9;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.answer-form button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.feedback {
  font-size: 1.4rem;
  font-weight: bold;
}

.feedback.correct {
  color: #2d8a4e;
}

.feedback.wrong {
  color: #cc3333;
}
</style>
