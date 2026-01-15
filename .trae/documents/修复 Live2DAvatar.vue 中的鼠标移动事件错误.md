## 问题分析

在 Live2DAvatar.vue 文件的第463行，onMouseMove 函数中出现了以下错误：

```
Uncaught TypeError: Cannot read properties of undefined (reading 'ParamAngleX')
```

错误原因是：代码检查了 `model.value.internalModel` 是否存在，但是没有检查 `params` 是否存在，导致在访问 `params['ParamAngleX']` 时出现了错误。

## 解决方案

在 `onMouseMove` 函数中，在访问 `params['ParamAngleX']` 和 `params['ParamAngleY']` 之前，添加一个检查，确保 `params` 存在。

## 修复步骤

1. 打开 Live2DAvatar.vue 文件
2. 找到 onMouseMove 函数（第439-470行）
3. 在 `const params = model.value.internalModel.parameters;` 之后，添加一个检查 `if (params) { ... }`
4. 将访问 `params['ParamAngleX']` 和 `params['ParamAngleY']` 的代码放在这个检查内部

## 修复后的代码

```javascript
// 应用旋转
if (model.value.internalModel) {
  const params = model.value.internalModel.parameters;
  if (params) {
    if (params['ParamAngleX']) {
      params['ParamAngleX'] = rotationX;
    }
    if (params['ParamAngleY']) {
      params['ParamAngleY'] = rotationY;
    }
  }
}
```

这样，当 `params` 不存在时，代码会跳过访问其中的属性，避免出现错误。