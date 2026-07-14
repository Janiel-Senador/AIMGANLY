<?php

declare(strict_types=1);

use Dotenv\Dotenv;

$vendorAutoload = __DIR__ . DIRECTORY_SEPARATOR . 'vendor' . DIRECTORY_SEPARATOR . 'autoload.php';
if (is_file($vendorAutoload)) {
    require_once $vendorAutoload;
}

spl_autoload_register(static function (string $class): void {
    if (!str_starts_with($class, 'App\\')) {
        return;
    }

    $relative = substr($class, 4);
    $path = __DIR__ . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . str_replace('\\', DIRECTORY_SEPARATOR, $relative) . '.php';
    if (is_file($path)) {
        require_once $path;
    }
});

if (class_exists(Dotenv::class)) {
    $rootEnvPath = dirname(__DIR__);
    if (is_file($rootEnvPath . DIRECTORY_SEPARATOR . '.env')) {
        Dotenv::createImmutable($rootEnvPath)->safeLoad();
    }
}

date_default_timezone_set('Asia/Manila');
