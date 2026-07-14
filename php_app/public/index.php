<?php

declare(strict_types=1);

use App\Config;
use App\GeminiClient;
use App\InventoryStore;
use App\NotesParser;
use App\PdrnExporter;

require_once dirname(__DIR__) . DIRECTORY_SEPARATOR . 'bootstrap.php';

session_start();
InventoryStore::ensureStorage();

$users = Config::users();
$flash = $_SESSION['flash'] ?? '';
unset($_SESSION['flash']);

if (isset($_GET['download']) && isset($_SESSION['user'])) {
    $record = InventoryStore::getRecord((string) $_GET['download']);
    $path = $record['generated_file_path'] ?? '';
    if ($record && is_string($path) && is_file($path)) {
        header('Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        header('Content-Disposition: attachment; filename="' . basename((string) ($record['generated_file_name'] ?? 'pdrn.xlsx')) . '"');
        readfile($path);
        exit;
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = (string) ($_POST['action'] ?? '');

    if ($action === 'login') {
        $email = strtolower(trim((string) ($_POST['email'] ?? '')));
        $password = (string) ($_POST['password'] ?? '');
        $user = $users[$email] ?? null;
        if ($user && $user['password'] === $password) {
            $_SESSION['user'] = ['email' => $email, 'role' => $user['role'], 'name' => $user['name']];
            header('Location: ./');
            exit;
        }
        $flash = 'Invalid email or password.';
    }

    if ($action === 'logout') {
        $_SESSION = [];
        session_destroy();
        header('Location: ./');
        exit;
    }

    $authUser = $_SESSION['user'] ?? null;
    if ($authUser) {
        if ($action === 'submit_notes') {
            $notes = trim((string) ($_POST['ci_notes'] ?? ''));
            if ($notes === '') {
                $flash = 'Please paste the CI notes before submitting.';
            } else {
                $parsed = NotesParser::parseCiNotes($notes);
                $record = InventoryStore::createCiSubmission($notes, $authUser, $parsed);
                $_SESSION['flash'] = 'Notes submitted successfully. Record ID: ' . $record['id'];
                header('Location: ./');
                exit;
            }
        }

        if ($action === 'generate_workbook' && $authUser['role'] === 'ao') {
            $recordId = (string) ($_POST['record_id'] ?? '');
            $templateKey = (string) ($_POST['template_key'] ?? 'bpi');
            $record = InventoryStore::getRecord($recordId);
            if ($record) {
                $parsed = $record['parsed_data'] ?? NotesParser::parseCiNotes((string) ($record['ci_notes'] ?? ''));
                $parsed['field_investigator'] = trim((string) ($_POST['field_investigator'] ?? $authUser['name']));
                $parsed['requesting_officer'] = trim((string) ($_POST['requesting_officer'] ?? $authUser['name']));
                [$path, $filename] = PdrnExporter::export($parsed, $templateKey);
                InventoryStore::updateRecord($recordId, [
                    'status' => 'generated_by_ao',
                    'parsed_data' => $parsed,
                    'template_key' => $templateKey,
                    'template_label' => Config::templateDefinitions()[$templateKey]['label'] ?? strtoupper($templateKey),
                    'ao_email' => $authUser['email'],
                    'ao_name' => $authUser['name'],
                    'ao_generated_at' => InventoryStore::nowIso(),
                    'generated_file_name' => $filename,
                    'generated_file_path' => $path,
                ]);
                $_SESSION['flash'] = 'Workbook generated successfully.';
                header('Location: ./?record=' . urlencode($recordId));
                exit;
            }
        }

        if ($action === 'submit_to_officer' && $authUser['role'] === 'ao') {
            $recordId = (string) ($_POST['record_id'] ?? '');
            InventoryStore::updateRecord($recordId, [
                'status' => 'submitted_to_officer',
                'submitted_to_officer_at' => InventoryStore::nowIso(),
            ]);
            $_SESSION['flash'] = 'Record submitted to Officer.';
            header('Location: ./?record=' . urlencode($recordId));
            exit;
        }

        if ($action === 'analyze_image' && $authUser['role'] === 'officer') {
            $image = $_FILES['inspection_image'] ?? null;
            if ($image && is_uploaded_file($image['tmp_name'])) {
                $analysis = GeminiClient::analyzeImage(
                    Config::geminiApiKey(),
                    (string) file_get_contents($image['tmp_name']),
                    (string) ($image['type'] ?: 'image/jpeg'),
                    (string) ($_POST['company_name'] ?? 'Your Company'),
                    $authUser['name'],
                    (string) ($_POST['inspection_context'] ?? ''),
                    isset($_POST['strict_mode'])
                );
                $_SESSION['analysis_result'] = $analysis;
            } else {
                $_SESSION['analysis_result'] = ['error' => 'Please upload an inspection image.'];
            }
            header('Location: ./');
            exit;
        }
    }
}

$authUser = $_SESSION['user'] ?? null;
$analysisResult = $_SESSION['analysis_result'] ?? null;

function h(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES, 'UTF-8');
}

function renderRecordTitle(array $record): string
{
    $applicant = $record['applicant_name'] ?: ($record['account_name'] ?: 'Unnamed Applicant');
    return $record['id'] . ' | ' . $applicant . ' | ' . strtoupper((string) ($record['status'] ?? ''));
}
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AIMGANLY PHP</title>
    <style>
        body{font-family:Arial,sans-serif;background:#09111f;color:#e8eef8;margin:0}
        .wrap{max-width:1200px;margin:0 auto;padding:24px}
        .card{background:#111b2f;border:1px solid rgba(255,255,255,.1);border-radius:16px;padding:18px;margin-bottom:16px}
        .hero{background:#0f1a31;border-radius:20px;padding:24px;margin-bottom:18px}
        h1,h2,h3{margin-top:0;color:#fff}
        input,textarea,select{width:100%;padding:10px;border-radius:10px;border:1px solid #334155;background:#0b1220;color:#fff;box-sizing:border-box}
        textarea{min-height:140px}
        button{background:#2563eb;color:#fff;border:none;border-radius:10px;padding:10px 14px;font-weight:700;cursor:pointer}
        .muted{color:#b8c7de}
        .grid{display:grid;gap:16px}
        .grid-2{grid-template-columns:1fr 1fr}
        .grid-3{grid-template-columns:repeat(3,1fr)}
        .note{white-space:pre-wrap;background:#0b1220;padding:12px;border-radius:12px;border:1px solid #1e293b}
        a{color:#93c5fd}
        .flash{padding:12px 14px;background:#16335f;border-radius:12px;margin-bottom:16px}
        details summary{cursor:pointer;font-weight:700}
        @media (max-width: 900px){.grid-2,.grid-3{grid-template-columns:1fr}}
    </style>
</head>
<body>
<div class="wrap">
    <div class="hero">
        <h1>AIMGANLY PHP</h1>
        <p class="muted">PHP rewrite of the CI - AO - Officer workflow with PDRN generation and Gemini image analysis.</p>
    </div>

    <?php if ($flash !== ''): ?>
        <div class="flash"><?= h($flash) ?></div>
    <?php endif; ?>

    <?php if (!$authUser): ?>
        <div class="card" style="max-width:480px">
            <h2>Sign In</h2>
            <form method="post">
                <input type="hidden" name="action" value="login">
                <div style="margin-bottom:12px">
                    <label>Email</label>
                    <input type="email" name="email" required>
                </div>
                <div style="margin-bottom:12px">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit">Sign In</button>
            </form>
        </div>
    <?php else: ?>
        <div class="card">
            <div class="grid grid-2">
                <div>
                    <strong><?= h($authUser['name']) ?></strong><br>
                    <span class="muted">Role: <?= strtoupper(h($authUser['role'])) ?></span>
                </div>
                <div style="text-align:right">
                    <form method="post">
                        <input type="hidden" name="action" value="logout">
                        <button type="submit">Sign Out</button>
                    </form>
                </div>
            </div>
        </div>

        <?php if ($authUser['role'] === 'ci'): ?>
            <?php $records = InventoryStore::listRecordsForUser('ci', $authUser['email']); ?>
            <div class="grid grid-2">
                <div class="card">
                    <h2>Submit CI Notes</h2>
                    <form method="post">
                        <input type="hidden" name="action" value="submit_notes">
                        <textarea name="ci_notes" placeholder="Paste the full CI notes here."></textarea>
                        <div style="margin-top:12px"><button type="submit">Submit Notes to AO Queue</button></div>
                    </form>
                </div>
                <div class="card">
                    <h2>My Submission History</h2>
                    <?php foreach ($records as $record): ?>
                        <details class="card">
                            <summary><?= h(renderRecordTitle($record)) ?></summary>
                            <div class="note" style="margin-top:12px"><?= h((string) $record['ci_notes']) ?></div>
                        </details>
                    <?php endforeach; ?>
                </div>
            </div>
        <?php elseif ($authUser['role'] === 'ao'): ?>
            <?php
            $records = InventoryStore::listRecordsForUser('ao', $authUser['email']);
            $selectedId = (string) ($_GET['record'] ?? ($records[0]['id'] ?? ''));
            $selectedRecord = $selectedId !== '' ? InventoryStore::getRecord($selectedId) : null;
            ?>
            <div class="grid grid-2">
                <div class="card">
                    <h2>Submission Queue</h2>
                    <?php foreach ($records as $record): ?>
                        <div style="margin-bottom:10px">
                            <a href="./?record=<?= urlencode((string) $record['id']) ?>"><?= h(renderRecordTitle($record)) ?></a>
                        </div>
                    <?php endforeach; ?>
                </div>
                <div class="card">
                    <h2>AO Workspace</h2>
                    <?php if ($selectedRecord): ?>
                        <?php $parsed = $selectedRecord['parsed_data'] ?? NotesParser::parseCiNotes((string) $selectedRecord['ci_notes']); ?>
                        <p><strong><?= h(renderRecordTitle($selectedRecord)) ?></strong></p>
                        <details open>
                            <summary>CI Notes Preview</summary>
                            <div class="note" style="margin-top:12px"><?= h((string) $selectedRecord['ci_notes']) ?></div>
                        </details>
                        <form method="post" style="margin-top:16px">
                            <input type="hidden" name="action" value="generate_workbook">
                            <input type="hidden" name="record_id" value="<?= h((string) $selectedRecord['id']) ?>">
                            <div class="grid grid-3">
                                <div>
                                    <label>Template</label>
                                    <select name="template_key">
                                        <?php foreach (Config::templateDefinitions() as $key => $definition): ?>
                                            <option value="<?= h($key) ?>" <?= ($selectedRecord['template_key'] ?? '') === $key ? 'selected' : '' ?>><?= h($definition['label']) ?></option>
                                        <?php endforeach; ?>
                                    </select>
                                </div>
                                <div>
                                    <label>Field Investigator</label>
                                    <input name="field_investigator" value="<?= h((string) ($parsed['field_investigator'] ?? $authUser['name'])) ?>">
                                </div>
                                <div>
                                    <label>Requesting Officer</label>
                                    <input name="requesting_officer" value="<?= h((string) ($parsed['requesting_officer'] ?? $authUser['name'])) ?>">
                                </div>
                            </div>
                            <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap">
                                <button type="submit">Generate Workbook</button>
                            </div>
                        </form>
                        <?php if (($selectedRecord['generated_file_path'] ?? '') !== ''): ?>
                            <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap">
                                <a href="./?download=<?= urlencode((string) $selectedRecord['id']) ?>">Download Current Workbook</a>
                                <form method="post">
                                    <input type="hidden" name="action" value="submit_to_officer">
                                    <input type="hidden" name="record_id" value="<?= h((string) $selectedRecord['id']) ?>">
                                    <button type="submit">Submit to Officer</button>
                                </form>
                            </div>
                        <?php endif; ?>
                    <?php else: ?>
                        <p class="muted">No AO records yet.</p>
                    <?php endif; ?>
                </div>
            </div>
        <?php else: ?>
            <?php $records = InventoryStore::listRecordsForUser('officer', $authUser['email']); ?>
            <div class="grid grid-2">
                <div class="card">
                    <h2>Officer Inbox</h2>
                    <?php foreach ($records as $record): ?>
                        <details class="card">
                            <summary><?= h(renderRecordTitle($record)) ?></summary>
                            <div style="margin-top:12px">
                                <a href="./?download=<?= urlencode((string) $record['id']) ?>">Download Workbook</a>
                            </div>
                            <details style="margin-top:12px">
                                <summary>CI Notes</summary>
                                <div class="note" style="margin-top:12px"><?= h((string) $record['ci_notes']) ?></div>
                            </details>
                        </details>
                    <?php endforeach; ?>
                </div>
                <div class="card">
                    <h2>AI Image Analyzer</h2>
                    <form method="post" enctype="multipart/form-data">
                        <input type="hidden" name="action" value="analyze_image">
                        <div style="margin-bottom:12px">
                            <label>Company Name</label>
                            <input name="company_name" value="Your Company">
                        </div>
                        <div style="margin-bottom:12px">
                            <label>Inspection Context</label>
                            <textarea name="inspection_context">Assess visible objects, structures, and materials. Highlight quality issues such as rust, damage, rot, moisture, wear, poor maintenance, or strong overall condition.</textarea>
                        </div>
                        <div style="margin-bottom:12px">
                            <label><input type="checkbox" name="strict_mode" checked> Use stricter quality ratings</label>
                        </div>
                        <div style="margin-bottom:12px">
                            <label>Inspection Image</label>
                            <input type="file" name="inspection_image" accept="image/*">
                        </div>
                        <button type="submit">Analyze Image</button>
                    </form>

                    <?php if (is_array($analysisResult)): ?>
                        <div class="card" style="margin-top:16px">
                            <h3>Analysis Result</h3>
                            <div class="note"><?= h(json_encode($analysisResult, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) ?></div>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        <?php endif; ?>
    <?php endif; ?>
</div>
</body>
</html>
