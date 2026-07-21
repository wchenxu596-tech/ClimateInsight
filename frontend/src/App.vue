<template>
  <div id="app">
    <el-container>
      <el-header class="header">
        <div class="logo">🌍 ClimateInsight</div>
        <nav class="nav-links">
          <router-link to="/" class="nav-item" active-class="nav-active">📊 总览</router-link>
          <router-link to="/trend" class="nav-item" active-class="nav-active">📈 趋势</router-link>
          <router-link to="/ranking" class="nav-item" active-class="nav-active">🏆 排名</router-link>
          <router-link to="/zones" class="nav-item" active-class="nav-active">🗺️ 气候带</router-link>
        </nav>
        <div class="year-picker">
          <el-select v-model="selectedYear" size="small" @change="onYearChange" style="width:100px">
            <el-option v-for="y in availableYears" :key="y" :label="y + '年'" :value="y" />
          </el-select>
        </div>
      </el-header>
      <el-main><router-view :key="$route.path + selectedYear" /></el-main>
    </el-container>

    <!-- 全局悬浮AI助手 -->
    <BIAgent />
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import BIAgent from './views/BIAgent.vue'

const availableYears = [2022, 2023, 2024]
const selectedYear = ref(2024)
provide('selectedYear', selectedYear)

function onYearChange(year) {
  selectedYear.value = year
}
</script>

<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Microsoft YaHei',sans-serif;background:#f0f2f5}
.header{background:linear-gradient(135deg,#1a237e,#0d47a1,#01579b);padding:0 20px;display:flex;align-items:center;height:56px!important}
.logo{color:#fff;font-size:20px;font-weight:bold;margin-right:32px;white-space:nowrap;flex-shrink:0}
.nav-links{display:flex;align-items:center;gap:4px;height:100%}
.nav-item{color:rgba(255,255,255,.75);font-size:15px;text-decoration:none;padding:0 16px;height:100%;display:flex;align-items:center;border-bottom:2px solid transparent;transition:all .2s;white-space:nowrap}
.nav-item:hover,.nav-active{color:#fff!important;background:rgba(255,255,255,.1);border-bottom-color:#64b5f6}
.year-picker{margin-left:auto;flex-shrink:0}
.el-main{padding:20px;min-height:calc(100vh - 56px)}
</style>
