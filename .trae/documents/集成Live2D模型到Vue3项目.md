# 集成Live2D模型到Vue3项目

## 步骤1：修改index.html文件
- 在index.html中引入live2d的核心脚本文件
- 路径：`/cubism-sdk/live2d.min.js` 和 `/cubism-sdk/live2dcubismcore.min.js`

## 步骤2：创建Live2D组件
- 在 `src/components` 目录下创建一个新的组件文件 `Live2DAvatar.vue`
- 实现组件的基本结构，包括canvas元素
- 引入必要的依赖：`PIXI` 和 `Live2DModel`

## 步骤3：实现组件逻辑
- 在组件中创建PIXI应用实例
- 实现模型加载函数 `loadModel`
- 配置模型路径为 `/live2d-models/hiyori_pro_zh/hiyori_pro_t11.model3.json`
- 实现模型的自动交互功能
- 添加点击事件监听，触发模型动作
- 实现组件的生命周期管理，包括挂载和卸载

## 步骤4：在主应用中使用组件
- 修改 `src/App.vue` 文件，引入并使用 `Live2DAvatar` 组件
- 调整组件的样式和位置

## 步骤5：测试和调试
- 运行开发服务器，检查模型是否正常加载和显示
- 测试模型的交互功能，确保点击时能够触发动作
- 调整模型的缩放比例和位置，使其在页面中显示合适

## 技术要点
- 使用 `pixi.js@7.4.3` 和 `pixi-live2d-display@0.5.0-beta` 来加载和渲染Live2D模型
- 利用Vue3的组合式API来管理组件的状态和生命周期
- 确保正确配置模型路径和缩放比例，以获得最佳显示效果
- 实现适当的错误处理，确保模型加载失败时不会影响应用的正常运行