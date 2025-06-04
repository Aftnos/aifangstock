<?php
// 设置响应头为纯文本
header('Content-Type: text/plain; charset=utf-8');

// 错误处理
set_error_handler(function($severity, $message, $file, $line) {
    echo "错误: $message\n";
    exit(1);
});

try {
    // 获取参数
    $license_type = isset($_GET['type'])     ? $_GET['type']     : 'standard';
    $duration     = isset($_GET['duration']) ? (int)$_GET['duration'] : 365;
    $count        = isset($_GET['count'])    ? (int)$_GET['count']    : 1;

    if ($count < 1 || $count > 100) {
        throw new Exception('生成数量必须在1-100之间');
    }
    if ($duration < 1 || $duration > 3650) {
        throw new Exception('授权时长必须在1-3650天之间');
    }

    // MySQL 数据库配置（请替换为实际值）
    $dbHost = 'localhost';
    $dbUser = 'app';
    $dbPass = 'app';
    $dbName = 'app';

    mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
    $db = new mysqli($dbHost, $dbUser, $dbPass, $dbName);
    $db->set_charset('utf8mb4');

    // 确保表存在
    ensure_tables_exist($db);

    // 生成并保存激活码
    $codes = [];
    $stmt = $db->prepare('INSERT INTO activation_codes (code, license_type, duration) VALUES (?, ?, ?)');
    for ($i = 0; $i < $count; $i++) {
        $code = generate_code();
        $codes[] = $code;
        $stmt->bind_param('ssi', $code, $license_type, $duration);
        $stmt->execute();
    }
    $stmt->close();
    $db->close();

    // 输出结果
    echo "成功生成 {$count} 个激活码 (类型: {$license_type}, 有效期: {$duration} 天):\n\n";
    foreach ($codes as $c) {
        echo $c . "\n";
    }

} catch (Exception $e) {
    echo "错误: " . $e->getMessage() . "\n";
    exit(1);
}

/**
 * 确保数据库表存在
 */
function ensure_tables_exist(mysqli $db) {
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
 * 生成随机激活码
 */
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
