<template>
  <div id="app">
    <el-container>
      <el-header class="header">
        <div class="logo">🌍 ClimateInsight</div>
        <el-menu :default-active="$route.path" mode="horizontal" router>
          <el-menu-item index="/">📊 总览</el-menu-item>
          <el-menu-item index="/trend">📈 趋势</el-menu-item>
          <el-menu-item index="/ranking">🏆 排名</el-menu-item>
          <el-menu-item index="/zones">🗺️ 气候带</el-menu-item>
          <el-menu-item index="/ai">🤖 AI问答</el-menu-item>
        </el-menu>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </div>
</template>

<script setup></script>

<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Microsoft YaHei',sans-serif;background:#f0f2f5}
.header{background:linear-gradient(135deg,#1a237e,#0d47a1,#01579b);padding:0 20px;display:flex;align-items:center;height:56px!important}
.logo{color:#fff;font-size:20px;font-weight:bold;margin-right:40px}
.el-menu{background:transparent!important;border-bottom:none!important}
.el-menu-item{color:rgba(255,255,255,.75)!important;font-size:15px!important;border-bottom:2px solid transparent!important;height:56px!important;line-height:56px!important}
.el-menu-item:hover,.el-menu-item.is-active{color:#fff!important;background:rgba(255,255,255,.1)!important;border-bottom-color:#64b5f6!important}
.el-main{padding:20px;min-height:calc(100vh - 56px)}
</style>
