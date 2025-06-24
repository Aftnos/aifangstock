<?php
/**
 * 简化版 “艾方存货管家” 更新服务器
 * 接口：check、download、stats、upload
 * 要求：PHP 7.0+，在项目根目录下创建 updates 目录，并赋予可写权限
 */

// 响应 JSON
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') exit(0);

// 路径配置
define('UPDATES_DIR', __DIR__ . '/updates');
define('VERSION_FILE', UPDATES_DIR . '/version.json');
define('LOG_DIR', __DIR__ . '/logs');

// 确保目录存在
foreach ([UPDATES_DIR, LOG_DIR] as $dir) {
    if (!is_dir($dir)) mkdir($dir, 0755, true);
}

// 读取请求
$input = json_decode(file_get_contents('php://input'), true) ?: $_POST;

// 路由分发
$action = $input['action'] ?? '';
switch ($action) {
    case 'check':    handleCheck($input);    break;
    case 'download': handleDownload($input); break;
    case 'stats':    handleStats($input);    break;
    case 'upload':   handleUpload();         break;
    default:
        sendJSON(['status'=>'error','message'=>'未知 action']);
}

/**
 * 检查更新
 */
function handleCheck($req) {
    $clientVer = $req['version'] ?? '0.0.0';
    $clientId  = $req['client_id'] ?? 'unknown';
    $latest    = getLatestVersion();
    if (!$latest) {
        return sendJSON(['status'=>'error','message'=>'无法获取版本信息']);
    }
    $need = version_compare($latest['version'], $clientVer, '>');

    logLine('check.log', [$clientId, $clientVer, $latest['version'], $need?'yes':'no']);

    $resp = [
        'status'=>'success',
        'update_available'=>$need,
        'version'=>$latest['version'],
        'min_required'=>$latest['min_required'] ?? '0.0.0'
    ];
    if ($need) {
        $resp += [
            'description'=>$latest['description']??'',
            'changelog'=>$latest['changelog']??'',
            'download_url'=>$latest['download_url']??'',
            'release_date'=>$latest['release_date']??'',
            'size'=>$latest['size']??0,
            'force_update'=> version_compare($latest['min_required']??'0.0.0',$clientVer,'>')
        ];
    }
    sendJSON($resp);
}

/**
 * 下载更新
 */
function handleDownload($req) {
    $ver = $req['version'] ?? '';
    $clientId = $req['client_id'] ?? 'unknown';
    if (!$ver) {
        return sendJSON(['status'=>'error','message'=>'未指定 version']);
    }
    $info = getVersionInfo($ver);
    if (!$info || empty($info['file_path'])) {
        return sendJSON(['status'=>'error','message'=>'版本不存在']);
    }
    logLine('download.log', [$clientId, $ver]);
    sendJSON(['status'=>'success','download_url'=>$info['download_url']]);
}

/**
 * 统计事件
 */
function handleStats($req) {
    logLine('stats.log', [
        $req['client_id']??'unknown',
        $req['version']   ??'unknown',
        $req['event']     ??'unknown',
        json_encode($req['data']??[], JSON_UNESCAPED_UNICODE)
    ]);
    sendJSON(['status'=>'success']);
}

/**
 * 上传新版本（开发者通过 multipart/form-data 上传）
 * 字段：file（zip），version, min_required, description, changelog, release_date, size
 */
function handleUpload() {
    if (empty($_FILES['file']) || empty($_POST['version'])) {
        return sendJSON(['status'=>'error','message'=>'参数不全']);
    }
    $ver = preg_replace('/[^\d\.]/','', $_POST['version']);
    $destName = "package-{$ver}.zip";
    $destPath = UPDATES_DIR . '/' . $destName;
    if (!move_uploaded_file($_FILES['file']['tmp_name'], $destPath)) {
        return sendJSON(['status'=>'error','message'=>'文件保存失败']);
    }
    // 构造版本条目
    $entry = [
        'version'      => $ver,
        'min_required' => $_POST['min_required'] ?? $ver,
        'description'  => $_POST['description']  ?? '',
        'changelog'    => $_POST['changelog']    ?? '',
        'download_url' => ($_SERVER['REQUEST_SCHEME']??'https').'://'.$_SERVER['HTTP_HOST']
                          .dirname($_SERVER['REQUEST_URI'])."/updates/{$destName}",
        'file_path'    => "/updates/{$destName}",
        'release_date' => $_POST['release_date'] ?? date('Y-m-d'),
        'size'         => intval($_POST['size']   ?? filesize($destPath))
    ];
    // 写入 version.json
    $all = is_file(VERSION_FILE) 
        ? json_decode(file_get_contents(VERSION_FILE), true) : ['versions'=>[]];
    // 覆盖或追加
    $found = false;
    foreach ($all['versions'] as &$v) {
        if ($v['version']===$ver) { $v=$entry; $found=true; break; }
    }
    if (!$found) $all['versions'][] = $entry;
    // 更新 latest 字段
    usort($all['versions'], fn($a,$b)=> version_compare($b['version'],$a['version']));
    $all['latest'] = $all['versions'][0]['version'];
    file_put_contents(VERSION_FILE, json_encode($all, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));
    sendJSON(['status'=>'success','message'=>"版本 {$ver} 上传成功"]);
}

/** 获取最新版本的完整信息 */
function getLatestVersion(): ?array {
    $data = is_file(VERSION_FILE)
        ? json_decode(file_get_contents(VERSION_FILE), true)
        : null;
    if (empty($data['versions'])) return null;
    // 保证已排序
    usort($data['versions'], fn($a,$b)=> version_compare($b['version'],$a['version']));
    return $data['versions'][0];
}

/** 根据版本号查找信息 */
function getVersionInfo(string $ver): ?array {
    $data = is_file(VERSION_FILE)
        ? json_decode(file_get_contents(VERSION_FILE), true)
        : null;
    if (empty($data['versions'])) return null;
    foreach ($data['versions'] as $v) {
        if ($v['version'] === $ver) return $v;
    }
    return null;
}

/** 追加日志行 */
function logLine(string $file, array $fields) {
    $time = date('Y-m-d H:i:s');
    $line = $time . '|' . implode('|', $fields) . "\n";
    file_put_contents(LOG_DIR."/{$file}", $line, FILE_APPEND);
}

/** 输出 JSON 并终止 */
function sendJSON($obj) {
    echo json_encode($obj, JSON_UNESCAPED_UNICODE);
    exit;
}
