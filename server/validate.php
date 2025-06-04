<?php
// 设置响应头为JSON
header('Content-Type: application/json; charset=utf-8');

// 错误处理
set_error_handler(function($severity, $message, $file, $line) {
    throw new ErrorException($message, 0, $severity, $file, $line);
});

try {
    // MySQL 数据库配置（请替换为实际值）
    $dbHost = 'localhost';
    $dbUser = 'app';
    $dbPass = 'app';
    $dbName = 'app';

    // 开启 mysqli 异常模式
    mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
    $db = new mysqli($dbHost, $dbUser, $dbPass, $dbName);
    $db->set_charset('utf8mb4');

    // 确保数据库表存在
    ensure_tables_exist($db);

    // 读取 POST 数据
    $json_data = file_get_contents('php://input');
    $request = json_decode($json_data, true);

    if (!$request) {
        throw new Exception('无效的请求数据');
    }

    // 获取请求动作
    $action = isset($request['action']) ? $request['action'] : '';

    switch ($action) {
        case 'activate':
            handle_activation($db, $request);
            break;

        case 'check_hardware':
            check_hardware_activation($db, $request);
            break;

        case 'check':
            // 兼容更新检查 API
            echo json_encode([
                'status' => 'success',
                'update_available' => false,
                'message' => '当前已是最新版本'
            ]);
            exit;

        default:
            throw new Exception('未知的操作类型');
    }

    $db->close();

} catch (Exception $e) {
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage()
    ]);
    exit;
}

/**
 * 确保数据库表存在
 * @param mysqli $db
 */
function ensure_tables_exist(mysqli $db) {
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

/**
 * 处理激活请求
 */
function handle_activation(mysqli $db, array $request) {
    if (empty($request['activation_code']) || empty($request['hardware_id'])) {
        throw new Exception('缺少必要的参数');
    }
    $activation_code = $request['activation_code'];
    $hardware_id     = $request['hardware_id'];

    // 查询激活码
    $stmt = $db->prepare('SELECT code, license_type, duration, is_used FROM activation_codes WHERE code = ?');
    $stmt->bind_param('s', $activation_code);
    $stmt->execute();
    $code_data = $stmt->get_result()->fetch_assoc();
    $stmt->close();

    if (!$code_data) {
        throw new Exception('无效的激活码');
    }
    if ($code_data['is_used']) {
        // 已用：检查是否同一硬件
        $stmt = $db->prepare('SELECT hardware_id FROM activations WHERE activation_code = ?');
        $stmt->bind_param('s', $activation_code);
        $stmt->execute();
        $activation = $stmt->get_result()->fetch_assoc();
        $stmt->close();

        if ($activation && $activation['hardware_id'] !== $hardware_id) {
            throw new Exception('此激活码已被使用');
        }
    }

    // 计算过期时间
    $duration    = (int)$code_data['duration'];
    $expiry_date = date('Y-m-d H:i:s', strtotime("+{$duration} days"));
    $license_type = $code_data['license_type'];

    // 检查是否已有此硬件的记录
    $stmt = $db->prepare('SELECT id FROM activations WHERE hardware_id = ?');
    $stmt->bind_param('s', $hardware_id);
    $stmt->execute();
    $existing = $stmt->get_result()->fetch_assoc();
    $stmt->close();

    if ($existing) {
        // 更新记录
        $stmt = $db->prepare(<<<SQL
UPDATE activations SET
    activation_code = ?,
    expiry_date = ?,
    license_type = ?,
    activated_at = CURRENT_TIMESTAMP
WHERE hardware_id = ?
SQL
        );
        $stmt->bind_param('ssss', $activation_code, $expiry_date, $license_type, $hardware_id);
    } else {
        // 插入新记录
        $stmt = $db->prepare(<<<SQL
INSERT INTO activations (hardware_id, activation_code, expiry_date, license_type)
VALUES (?, ?, ?, ?)
SQL
        );
        $stmt->bind_param('ssss', $hardware_id, $activation_code, $expiry_date, $license_type);
    }
    $stmt->execute();
    $stmt->close();

    // 标记激活码为已用
    $stmt = $db->prepare('UPDATE activation_codes SET is_used = 1 WHERE code = ?');
    $stmt->bind_param('s', $activation_code);
    $stmt->execute();
    $stmt->close();

    // 返回成功
    echo json_encode([
        'status'      => 'success',
        'message'     => '激活成功',
        'expiry_date' => $expiry_date,
        'license_type'=> $license_type
    ]);
}

/**
 * 检查硬件激活状态
 */
function check_hardware_activation(mysqli $db, array $request) {
    if (empty($request['hardware_id'])) {
        throw new Exception('缺少硬件ID参数');
    }
    $hardware_id = $request['hardware_id'];

    $stmt = $db->prepare('SELECT expiry_date, license_type FROM activations WHERE hardware_id = ?');
    $stmt->bind_param('s', $hardware_id);
    $stmt->execute();
    $activation = $stmt->get_result()->fetch_assoc();
    $stmt->close();

    if ($activation) {
        $now = date('Y-m-d H:i:s');
        if (strtotime($now) > strtotime($activation['expiry_date'])) {
            echo json_encode([
                'status'    => 'success',
                'activated' => false,
                'message'   => '授权已过期'
            ]);
        } else {
            echo json_encode([
                'status'      => 'success',
                'activated'   => true,
                'expiry_date' => $activation['expiry_date'],
                'license_type'=> $activation['license_type'],
                'message'     => '授权有效'
            ]);
        }
    } else {
        echo json_encode([
            'status'    => 'success',
            'activated' => false,
            'message'   => '未找到激活记录'
        ]);
    }
}
