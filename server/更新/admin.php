<?php
/**
 * update_admin.php — 更新包管理后台（版本号三段式输入）
 */

define('UPDATES_DIR', __DIR__ . '/updates');
define('VERSION_FILE', UPDATES_DIR . '/version.json');
define('LOG_DIR', __DIR__ . '/logs');

// 确保目录存在
foreach ([UPDATES_DIR, LOG_DIR] as $d) {
    if (!is_dir($d)) mkdir($d, 0755, true);
}

// 加载或初始化版本数据
$versionsData = is_file(VERSION_FILE)
    ? json_decode(file_get_contents(VERSION_FILE), true)
    : ['latest'=>'','versions'=>[]];

// 处理表单提交
$message = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // 删除版本
    if (!empty($_POST['action']) && $_POST['action']==='delete' && !empty($_POST['version'])) {
        $ver = $_POST['version'];
        // 删除文件
        foreach ($versionsData['versions'] as $v) {
            if ($v['version']===$ver && !empty($v['file_path'])) {
                $fp = __DIR__ . $v['file_path'];
                if (is_file($fp)) unlink($fp);
            }
        }
        // 更新列表
        $versionsData['versions'] = array_values(array_filter(
            $versionsData['versions'],
            fn($v)=>$v['version']!==$ver
        ));
        usort($versionsData['versions'], fn($a,$b)=>version_compare($b['version'],$a['version']));
        $versionsData['latest'] = $versionsData['versions'][0]['version'] ?? '';
        file_put_contents(VERSION_FILE,
            json_encode($versionsData, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT)
        );
        $message = "版本 {$ver} 已删除。";
    }
    // 上传新版本
    if (!empty($_POST['action']) && $_POST['action']==='upload' && !empty($_FILES['file'])) {
        // 组合版本号
        $maj = $_POST['version_major'] ?? '';
        $min = $_POST['version_minor'] ?? '';
        $pat = $_POST['version_patch'] ?? '';
        $maj2 = $_POST['minreq_major'] ?? '';
        $min2 = $_POST['minreq_minor'] ?? '';
        $pat2 = $_POST['minreq_patch'] ?? '';
        if (!ctype_digit($maj)||!ctype_digit($min)||!ctype_digit($pat)
         || !ctype_digit($maj2)||!ctype_digit($min2)||!ctype_digit($pat2)) {
            $message = '上传失败：版本号和最低版本三段式输入均需填写非负整数。';
        } else {
            $ver      = "{$maj}.{$min}.{$pat}";
            $min_req  = "{$maj2}.{$min2}.{$pat2}";
            $destName = "package-{$ver}.zip";
            $destPath = UPDATES_DIR . '/' . $destName;
            if (move_uploaded_file($_FILES['file']['tmp_name'], $destPath)) {
                $size = filesize($destPath);
                $entry = [
                    'version'      => $ver,
                    'min_required' => $min_req,
                    'description'  => $_POST['description']  ?? '',
                    'changelog'    => $_POST['changelog']    ?? '',
                    'download_url' => ($_SERVER['REQUEST_SCHEME']??'https').'://'
                                      .$_SERVER['HTTP_HOST']
                                      .dirname($_SERVER['REQUEST_URI'])
                                      ."/updates/{$destName}",
                    'file_path'    => "/updates/{$destName}",
                    'release_date' => $_POST['release_date'] ?? date('Y-m-d'),
                    'size'         => $size
                ];
                // 更新或插入
                $found = false;
                foreach ($versionsData['versions'] as &$v) {
                    if ($v['version'] === $ver) {
                        $v = $entry; $found = true; break;
                    }
                }
                if (!$found) $versionsData['versions'][] = $entry;
                usort($versionsData['versions'], fn($a,$b)=>version_compare($b['version'],$a['version']));
                $versionsData['latest'] = $versionsData['versions'][0]['version'];
                file_put_contents(VERSION_FILE,
                    json_encode($versionsData, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT)
                );
                $message = "版本 {$ver} 上传成功（{$size} bytes）。";
            } else {
                $message = '上传失败：无法保存文件。';
            }
        }
    }
    // 刷新数据
    $versionsData = json_decode(file_get_contents(VERSION_FILE), true);
}
?>
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>更新包管理后台</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: "Segoe UI", Tahoma, sans-serif; background: #f2f4f7; color: #333; }
    .container { max-width: 900px; margin: 30px auto; padding: 20px;
                 background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-radius: 6px; }
    h1 { margin-bottom: 10px; }
    .msg { padding: 12px; background: #e3f2fd; border: 1px solid #90caf9;
           border-radius: 4px; margin-bottom: 20px; color: #1565c0; }
    .form-section { margin-bottom: 30px; }
    .form-group { display: flex; align-items: center; margin-bottom: 15px; }
    .form-group label { width: 120px; }
    .form-group input[type="number"],
    .form-group input[type="date"],
    .form-group textarea { padding: 8px; border: 1px solid #ccc;
                           border-radius: 4px; font-size: 1em; }
    .form-group .version-inputs { display: flex; gap: 8px; }
    .form-group .version-inputs input { width: 60px; }
    .form-group span { margin-left: 10px; font-size: 0.9em; color: #666; }
    button { padding: 8px 16px; border: none; border-radius: 4px;
             background: #1976d2; color: #fff; cursor: pointer; font-size: 1em; }
    button:hover { background: #1565c0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px; border: 1px solid #e0e0e0; text-align: left; }
    th { background: #1976d2; color: #fff; }
    tr:nth-child(even) { background: #f9f9f9; }
    .table-actions button { background: #e53935; }
    .table-actions button:hover { background: #c62828; }
  </style>
</head>
<body>
  <div class="container">
    <h1>更新包管理后台</h1>
    <?php if($message): ?>
      <div class="msg"><?= htmlspecialchars($message) ?></div>
    <?php endif; ?>

    <section class="form-section">
      <h2>上传新版本</h2>
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="upload">
        <div class="form-group">
          <label>版本号：</label>
          <div class="version-inputs">
            <input type="number" name="version_major" min="0" placeholder="主" required>
            <input type="number" name="version_minor" min="0" placeholder="次" required>
            <input type="number" name="version_patch" min="0" placeholder="修" required>
          </div>
        </div>
        <div class="form-group">
          <label>最低版本：</label>
          <div class="version-inputs">
            <input type="number" name="minreq_major" min="0" placeholder="主" required>
            <input type="number" name="minreq_minor" min="0" placeholder="次" required>
            <input type="number" name="minreq_patch" min="0" placeholder="修" required>
          </div>
        </div>
        <div class="form-group">
          <label>发布日期：</label>
          <input type="date" name="release_date">
        </div>
        <div class="form-group">
          <label>安装包：</label>
          <input type="file" name="file" accept=".zip" required id="fileInput">
          <span id="filesize">未选择</span>
        </div>
        <div class="form-group">
          <label>描述：</label>
          <textarea name="description" rows="2"></textarea>
        </div>
        <div class="form-group">
          <label>更新日志：</label>
          <textarea name="changelog" rows="4"></textarea>
        </div>
        <button type="submit">上传</button>
      </form>
    </section>

    <section>
      <h2>已有版本列表（Latest: <?= htmlspecialchars($versionsData['latest']) ?>）</h2>
      <table>
        <tr>
          <th>版本</th><th>最低版本</th><th>发布日期</th><th>大小</th><th>下载</th><th>操作</th>
        </tr>
        <?php foreach($versionsData['versions'] as $v): ?>
        <tr>
          <td><?= htmlspecialchars($v['version']) ?></td>
          <td><?= htmlspecialchars($v['min_required'] ?? '') ?></td>
          <td><?= htmlspecialchars($v['release_date']) ?></td>
          <td><?= number_format($v['size']) ?> bytes</td>
          <td><a href="<?= htmlspecialchars($v['download_url']) ?>" target="_blank">下载</a></td>
          <td class="table-actions">
            <form method="post" style="display:inline"
                  onsubmit="return confirm('确认删除版本 <?= $v['version'] ?>？');">
              <input type="hidden" name="action" value="delete">
              <input type="hidden" name="version" value="<?= htmlspecialchars($v['version']) ?>">
              <button type="submit">删除</button>
            </form>
          </td>
        </tr>
        <?php endforeach; ?>
      </table>
    </section>
  </div>

  <script>
    document.getElementById('fileInput').addEventListener('change', function() {
      const span = document.getElementById('filesize');
      if (this.files.length) {
        span.textContent = this.files[0].size.toLocaleString() + ' bytes';
      } else {
        span.textContent = '未选择';
      }
    });
  </script>
</body>
</html>
