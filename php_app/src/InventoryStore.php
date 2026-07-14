<?php

declare(strict_types=1);

namespace App;

final class InventoryStore
{
    public static function ensureStorage(): void
    {
        if (!is_dir(Config::dataPath())) {
            mkdir(Config::dataPath(), 0777, true);
        }

        if (!is_dir(Config::exportPath())) {
            mkdir(Config::exportPath(), 0777, true);
        }

        if (!is_file(Config::inventoryPath())) {
            file_put_contents(
                Config::inventoryPath(),
                json_encode(['records' => []], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)
            );
        }
    }

    public static function nowIso(): string
    {
        return date('c');
    }

    public static function loadRecords(): array
    {
        self::ensureStorage();
        $payload = json_decode((string) file_get_contents(Config::inventoryPath()), true);
        $records = $payload['records'] ?? [];
        usort(
            $records,
            static fn (array $a, array $b): int => strcmp((string) ($b['updated_at'] ?? ''), (string) ($a['updated_at'] ?? ''))
        );

        return $records;
    }

    public static function saveRecords(array $records): void
    {
        self::ensureStorage();
        file_put_contents(
            Config::inventoryPath(),
            json_encode(['records' => array_values($records)], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)
        );
    }

    public static function getRecord(string $recordId): ?array
    {
        foreach (self::loadRecords() as $record) {
            if (($record['id'] ?? '') === $recordId) {
                return $record;
            }
        }

        return null;
    }

    public static function createCiSubmission(string $notes, array $user, array $parsed): array
    {
        $createdAt = self::nowIso();
        $record = [
            'id' => strtoupper(substr(bin2hex(random_bytes(8)), 0, 10)),
            'status' => 'submitted_to_ao',
            'template_key' => '',
            'template_label' => '',
            'ci_notes' => trim($notes),
            'parsed_data' => $parsed,
            'account_name' => $parsed['account_name'] ?? '',
            'applicant_name' => NotesParser::joinName(
                $parsed['subject_last_name'] ?? '',
                $parsed['subject_first_name'] ?? '',
                $parsed['subject_middle_name'] ?? ''
            ),
            'ci_submitter_email' => strtolower((string) ($user['email'] ?? '')),
            'ci_submitter_name' => $user['name'] ?? 'CI User',
            'ci_submitted_at' => $createdAt,
            'ao_email' => '',
            'ao_name' => '',
            'ao_generated_at' => '',
            'submitted_to_officer_at' => '',
            'generated_file_name' => '',
            'generated_file_path' => '',
            'created_at' => $createdAt,
            'updated_at' => $createdAt,
        ];

        $records = self::loadRecords();
        $records[] = $record;
        self::saveRecords($records);

        return $record;
    }

    public static function updateRecord(string $recordId, array $updates): ?array
    {
        $records = self::loadRecords();
        $updated = null;

        foreach ($records as $index => $record) {
            if (($record['id'] ?? '') !== $recordId) {
                continue;
            }

            $updated = array_merge($record, $updates, ['updated_at' => self::nowIso()]);
            $records[$index] = $updated;
            break;
        }

        if ($updated === null) {
            return null;
        }

        self::saveRecords($records);

        return $updated;
    }

    public static function listRecordsForUser(string $role, string $email): array
    {
        $email = strtolower(trim($email));
        $records = self::loadRecords();

        return match ($role) {
            'ci' => array_values(array_filter(
                $records,
                static fn (array $record): bool => strtolower((string) ($record['ci_submitter_email'] ?? '')) === $email
            )),
            'ao' => array_values(array_filter(
                $records,
                static fn (array $record): bool => in_array((string) ($record['status'] ?? ''), ['submitted_to_ao', 'generated_by_ao', 'submitted_to_officer'], true)
            )),
            'officer' => array_values(array_filter(
                $records,
                static fn (array $record): bool => ($record['status'] ?? '') === 'submitted_to_officer'
            )),
            default => $records,
        };
    }
}
