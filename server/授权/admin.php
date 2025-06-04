<?php
session_start();

$admin_username = '艾拉与方块';
$admin_password_hash = '$2y$10$eyPWnKKkpHN5ub98JUcMWuujGcS2wIknAlkKXpXZ4Tj4OVXmbTHHm';

// 处理登录请求
if (isset($_POST['login'])) {
    $inputUser = $_POST['username'] ?? '';
    $inputPass = $_POST['password'] ?? '';
    if ($inputUser === $admin_username && password_verify($inputPass, $admin_password_hash)) {
        $_SESSION['admin_logged_in'] = true;
    } else {
        $login_error = '用户名或密码错误';
    }
}

// 处理登出请求
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: admin.php');
    exit;
}

// 错误处理
set_error_handler(function($severity, $message, $file, $line) {
    throw new ErrorException($message, 0, $severity, $file, $line);
});

// 数据库连接函数
function connect_db() {
    $dbHost = 'localhost';
    $dbUser = 'app';
    $dbPass = 'app';
    $dbName = 'app';
    
    mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
    $db = new mysqli($dbHost, $dbUser, $dbPass, $dbName);
    $db->set_charset('utf8mb4');
    
    return $db;
}

// 确保数据库表存在
function ensure_tables_exist($db) {
    // 激活码表
    $db->query(<<<SQL
CREATE TABLE IF NOT EXISTS activation_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(255) NOT NULL UNIQUE,
    license_type VARCHAR(50) DEFAULT 'standard',
    duration INT DEFAULT 365,
    is_used TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
SQL
    );
    // 激活记录表
    $db->query(<<<SQL
CREATE TABLE IF NOT EXISTS activations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hardware_id VARCHAR(255) NOT NULL,
    activation_code VARCHAR(255) NOT NULL,
    expiry_date DATETIME NOT NULL,
    license_type VARCHAR(50) DEFAULT 'standard',
    activated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activation_code) REFERENCES activation_codes(code)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
SQL
    );
}

// 生成随机激活码
function generate_code() {
    $chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    $code = '';
    for ($group = 0; $group < 5; $group++) {
        for ($i = 0; $i < 5; $i++) {
            $code .= $chars[random_int(0, strlen($chars) - 1)];
        }
        if ($group < 4) {
            $code .= '-';
        }
    }
    return $code;
}

// 处理生成激活码请求
function handle_generate_codes($db) {
    $license_type = isset($_POST['license_type']) ? $_POST['license_type'] : 'standard';
    $duration = isset($_POST['duration']) ? (int)$_POST['duration'] : 365;
    $count = isset($_POST['count']) ? (int)$_POST['count'] : 1;
    
    if ($count < 1 || $count > 100) {
        return ['status' => 'error', 'message' => '生成数量必须在1-100之间'];
    }
    if ($duration < 1 || $duration > 3650) {
        return ['status' => 'error', 'message' => '授权时长必须在1-3650天之间'];
    }
    
    $codes = [];
    $stmt = $db->prepare('INSERT INTO activation_codes (code, license_type, duration) VALUES (?, ?, ?)');
    for ($i = 0; $i < $count; $i++) {
        $code = generate_code();
        $codes[] = $code;
        $stmt->bind_param('ssi', $code, $license_type, $duration);
        $stmt->execute();
    }
    $stmt->close();
    
    return ['status' => 'success', 'codes' => $codes, 'count' => $count, 'license_type' => $license_type, 'duration' => $duration];
}

// 获取激活码列表
function get_activation_codes($db, $limit = 100, $offset = 0, $filter = '') {
    $where = '';
    if ($filter === 'used') {
        $where = 'WHERE is_used = 1';
    } elseif ($filter === 'unused') {
        $where = 'WHERE is_used = 0';
    }
    
    $result = $db->query("SELECT * FROM activation_codes $where ORDER BY created_at DESC LIMIT $offset, $limit");
    $codes = [];
    while ($row = $result->fetch_assoc()) {
        $codes[] = $row;
    }
    return $codes;
}

// 获取激活记录列表
function get_activations($db, $limit = 100, $offset = 0) {
    $result = $db->query("SELECT a.*, c.license_type, c.code 
                         FROM activations a 
                         JOIN activation_codes c ON a.activation_code = c.code 
                         ORDER BY a.activated_at DESC LIMIT $offset, $limit");
    $activations = [];
    while ($row = $result->fetch_assoc()) {
        $activations[] = $row;
    }
    return $activations;
}

// 删除激活码
function delete_activation_code($db, $code_id) {
    $stmt = $db->prepare('DELETE FROM activation_codes WHERE id = ? AND is_used = 0');
    $stmt->bind_param('i', $code_id);
    $stmt->execute();
    $affected = $stmt->affected_rows;
    $stmt->close();
    
    return $affected > 0;
}

// 删除激活记录
function delete_activation($db, $activation_id) {
    // 首先获取激活记录信息
    $stmt = $db->prepare('SELECT activation_code FROM activations WHERE id = ?');
    $stmt->bind_param('i', $activation_id);
    $stmt->execute();
    $result = $stmt->get_result();
    $activation = $result->fetch_assoc();
    $stmt->close();
    
    if (!$activation) {
        return false;
    }
    
    // 开始事务
    $db->begin_transaction();
    
    try {
        // 删除激活记录
        $stmt = $db->prepare('DELETE FROM activations WHERE id = ?');
        $stmt->bind_param('i', $activation_id);
        $stmt->execute();
        $stmt->close();
        
        // 将对应的激活码标记为未使用
        $stmt = $db->prepare('UPDATE activation_codes SET is_used = 0 WHERE code = ?');
        $stmt->bind_param('s', $activation['activation_code']);
        $stmt->execute();
        $stmt->close();
        
        // 提交事务
        $db->commit();
        return true;
    } catch (Exception $e) {
        // 回滚事务
        $db->rollback();
        return false;
    }
}

// 处理请求
try {
    $result = null;
    $db = null;
    
    // 只有登录后才能执行操作
    if (isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true) {
        $db = connect_db();
        ensure_tables_exist($db);
        
        // 处理生成激活码请求
        if (isset($_POST['generate_codes'])) {
            $result = handle_generate_codes($db);
        }
        
        // 处理删除激活码请求
        if (isset($_POST['delete_code'])) {
            $code_id = (int)$_POST['code_id'];
            if (delete_activation_code($db, $code_id)) {
                $result = ['status' => 'success', 'message' => '激活码已删除'];
            } else {
                $result = ['status' => 'error', 'message' => '无法删除已使用的激活码'];
            }
        }
        
        // 处理删除激活记录请求
        if (isset($_POST['delete_activation'])) {
            $activation_id = (int)$_POST['activation_id'];
            if (delete_activation($db, $activation_id)) {
                $result = ['status' => 'success', 'message' => '激活记录已删除，对应的激活码已重置为未使用状态'];
            } else {
                $result = ['status' => 'error', 'message' => '删除激活记录失败'];
            }
        }
        
        // 获取激活码列表
        $filter = isset($_GET['filter']) ? $_GET['filter'] : '';
        $activation_codes = get_activation_codes($db, 100, 0, $filter);
        
        // 获取激活记录列表
        $activations = get_activations($db, 100);
        
        if ($db) {
            $db->close();
        }
    }
} catch (Exception $e) {
    $error_message = $e->getMessage();
    if ($db) {
        $db->close();
    }
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>密钥管理系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding-top: 20px; }
        .container { max-width: 1200px; }
        .code-block { word-break: break-all; }
        .tab-content { padding-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4 text-center">密钥管理系统</h1>
        
        <?php if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true): ?>
            <!-- 登录表单 -->
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">管理员登录</div>
                        <div class="card-body">
                            <?php if (isset($login_error)): ?>
                                <div class="alert alert-danger"><?php echo $login_error; ?></div>
                            <?php endif; ?>
                            
                            <form method="post">
                                <div class="mb-3">
                                    <label for="username" class="form-label">用户名</label>
                                    <input type="text" class="form-control" id="username" name="username" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">密码</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                <button type="submit" name="login" class="btn btn-primary">登录</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        <?php else: ?>
            <!-- 管理界面 -->
            <div class="d-flex justify-content-end mb-3">
                <a href="?logout=1" class="btn btn-outline-danger">退出登录</a>
            </div>
            
            <?php if (isset($error_message)): ?>
                <div class="alert alert-danger"><?php echo $error_message; ?></div>
            <?php endif; ?>
            
            <?php if (isset($result) && $result['status'] === 'error'): ?>
                <div class="alert alert-danger"><?php echo $result['message']; ?></div>
            <?php endif; ?>
            
            <?php if (isset($result) && $result['status'] === 'success' && isset($result['message'])): ?>
                <div class="alert alert-success"><?php echo $result['message']; ?></div>
            <?php endif; ?>
            
            <!-- 生成的激活码显示 -->
            <?php if (isset($result) && $result['status'] === 'success' && isset($result['codes'])): ?>
                <div class="alert alert-success">
                    <h4>成功生成 <?php echo $result['count']; ?> 个激活码</h4>
                    <p>类型: <?php echo $result['license_type']; ?>, 有效期: <?php echo $result['duration']; ?> 天</p>
                    <div class="code-block">
                        <?php foreach ($result['codes'] as $code): ?>
                            <code><?php echo $code; ?></code><br>
                        <?php endforeach; ?>
                    </div>
                </div>
            <?php endif; ?>
            
            <!-- 选项卡导航 -->
            <ul class="nav nav-tabs" id="myTab" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="generate-tab" data-bs-toggle="tab" data-bs-target="#generate" type="button" role="tab">生成激活码</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="codes-tab" data-bs-toggle="tab" data-bs-target="#codes" type="button" role="tab">激活码列表</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="activations-tab" data-bs-toggle="tab" data-bs-target="#activations" type="button" role="tab">激活记录</button>
                </li>
            </ul>
            
            <!-- 选项卡内容 -->
            <div class="tab-content" id="myTabContent">
                <!-- 生成激活码表单 -->
                <div class="tab-pane fade show active" id="generate" role="tabpanel">
                    <div class="card">
                        <div class="card-header">生成新的激活码</div>
                        <div class="card-body">
                            <form method="post">
                                <div class="mb-3">
                                    <label for="license_type" class="form-label">授权类型</label>
                                    <select class="form-select" id="license_type" name="license_type">
                                        <option value="standard">标准版</option>
                                        <option value="professional">专业版</option>
                                        <option value="enterprise">企业版</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label for="duration" class="form-label">有效期（天）</label>
                                    <input type="number" class="form-control" id="duration" name="duration" value="365" min="1" max="3650">
                                </div>
                                <div class="mb-3">
                                    <label for="count" class="form-label">生成数量</label>
                                    <input type="number" class="form-control" id="count" name="count" value="1" min="1" max="100">
                                </div>
                                <button type="submit" name="generate_codes" class="btn btn-primary">生成激活码</button>
                            </form>
                        </div>
                    </div>
                </div>
                
                <!-- 激活码列表 -->
                <div class="tab-pane fade" id="codes" role="tabpanel">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <span>激活码列表</span>
                            <div class="btn-group">
                                <a href="?filter=" class="btn btn-outline-secondary <?php echo !isset($_GET['filter']) || $_GET['filter'] === '' ? 'active' : ''; ?>">全部</a>
                                <a href="?filter=used" class="btn btn-outline-secondary <?php echo isset($_GET['filter']) && $_GET['filter'] === 'used' ? 'active' : ''; ?>">已使用</a>
                                <a href="?filter=unused" class="btn btn-outline-secondary <?php echo isset($_GET['filter']) && $_GET['filter'] === 'unused' ? 'active' : ''; ?>">未使用</a>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>激活码</th>
                                            <th>授权类型</th>
                                            <th>有效期(天)</th>
                                            <th>状态</th>
                                            <th>创建时间</th>
                                            <th>操作</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <?php if (isset($activation_codes) && !empty($activation_codes)): ?>
                                            <?php foreach ($activation_codes as $code): ?>
                                                <tr>
                                                    <td><?php echo $code['id']; ?></td>
                                                    <td><code><?php echo $code['code']; ?></code></td>
                                                    <td><?php echo $code['license_type']; ?></td>
                                                    <td><?php echo $code['duration']; ?></td>
                                                    <td>
                                                        <?php if ($code['is_used']): ?>
                                                            <span class="badge bg-success">已使用</span>
                                                        <?php else: ?>
                                                            <span class="badge bg-secondary">未使用</span>
                                                        <?php endif; ?>
                                                    </td>
                                                    <td><?php echo $code['created_at']; ?></td>
                                                    <td>
                                                        <?php if (!$code['is_used']): ?>
                                                            <form method="post" onsubmit="return confirm('确定要删除这个激活码吗？')">
                                                                <input type="hidden" name="code_id" value="<?php echo $code['id']; ?>">
                                                                <button type="submit" name="delete_code" class="btn btn-sm btn-danger">删除</button>
                                                            </form>
                                                        <?php endif; ?>
                                                    </td>
                                                </tr>
                                            <?php endforeach; ?>
                                        <?php else: ?>
                                            <tr>
                                                <td colspan="7" class="text-center">没有找到激活码记录</td>
                                            </tr>
                                        <?php endif; ?>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 激活记录列表 -->
                <div class="tab-pane fade" id="activations" role="tabpanel">
                    <div class="card">
                        <div class="card-header">激活记录列表</div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>硬件ID</th>
                                            <th>激活码</th>
                                            <th>授权类型</th>
                                            <th>过期时间</th>
                                            <th>激活时间</th>
                                            <th>操作</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <?php if (isset($activations) && !empty($activations)): ?>
                                            <?php foreach ($activations as $activation): ?>
                                                <tr>
                                                    <td><?php echo $activation['id']; ?></td>
                                                    <td><small class="text-muted"><?php echo $activation['hardware_id']; ?></small></td>
                                                    <td><code><?php echo $activation['code']; ?></code></td>
                                                    <td><?php echo $activation['license_type']; ?></td>
                                                    <td>
                                                        <?php 
                                                        $now = new DateTime();
                                                        $expiry = new DateTime($activation['expiry_date']);
                                                        $is_expired = $now > $expiry;
                                                        ?>
                                                        <span class="<?php echo $is_expired ? 'text-danger' : 'text-success'; ?>">
                                                            <?php echo $activation['expiry_date']; ?>
                                                            <?php if ($is_expired): ?>
                                                                <span class="badge bg-danger">已过期</span>
                                                            <?php endif; ?>
                                                        </span>
                                                    </td>
                                                    <td><?php echo $activation['activated_at']; ?></td>
                                                    <td>
                                                        <form method="post" onsubmit="return confirm('确定要删除这个激活记录吗？这将使对应的激活码可以重新使用。')">
                                                            <input type="hidden" name="activation_id" value="<?php echo $activation['id']; ?>">
                                                            <button type="submit" name="delete_activation" class="btn btn-sm btn-danger">删除</button>
                                                        </form>
                                                    </td>
                                                </tr>
                                            <?php endforeach; ?>
                                        <?php else: ?>
                                            <tr>
                                                <td colspan="7" class="text-center">没有找到激活记录</td>
                                            </tr>
                                        <?php endif; ?>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        <?php endif; ?>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>