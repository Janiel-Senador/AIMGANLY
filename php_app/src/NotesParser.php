<?php

declare(strict_types=1);

namespace App;

final class NotesParser
{
    public static function defaults(): array
    {
        return [
            'account_name' => '',
            'subject_last_name' => '',
            'subject_first_name' => '',
            'subject_middle_name' => '',
            'subject_bday_age' => '',
            'subject_birthplace' => '',
            'subject_civil_status' => '',
            'subject_nationality' => '',
            'subject_education' => '',
            'subject_employment' => '',
            'subject_business' => '',
            'subject_employer_name' => '',
            'subject_employer_address' => '',
            'subject_business_name' => '',
            'subject_business_address' => '',
            'spouse_last_name' => '',
            'spouse_first_name' => '',
            'spouse_middle_name' => '',
            'spouse_bday_age' => '',
            'spouse_civil_status' => '',
            'spouse_nationality' => '',
            'spouse_education' => '',
            'spouse_employment' => '',
            'spouse_business' => '',
            'spouse_employer_name' => '',
            'spouse_business_name' => '',
            'purpose_of_loan' => '',
            'dependents' => '',
            'given_address' => '',
            'verified_address' => '',
            'complete_address' => '',
            'present_address' => '',
            'previous_address' => '',
            'province' => '',
            'region' => '',
            'contact_number' => '',
            'length_of_stay' => '',
            'ownership' => '',
            'landlord_name' => '',
            'rental_fee' => '',
            'vehicle_unit_year_model' => '',
            'vehicle_owned_or_mortgage' => '',
            'vehicle_condition' => '',
            'vehicle_monthly_amortization' => '',
            'type_of_residence' => '',
            'no_of_storey' => '',
            'classification' => '',
            'made_of' => '',
            'appearance' => '',
            'accessibility' => '',
            'neighborhood' => '',
            'house_color' => '',
            'gate_color' => '',
            'fence_color' => '',
            'interior' => '',
            'exterior' => '',
            'lot_area' => '',
            'floor_area' => '',
            'landmark' => '',
            'corner' => '',
            'security_guard_hoa' => '',
            'time_of_visit' => '',
            'living_condition' => '',
            'remarks' => '',
            'ci_remarks_observation' => '',
            'barangay_informant_name' => '',
            'barangay_informant_position' => '',
            'barangay_subject_known' => '',
            'barangay_informant_address' => '',
            'neighbor_1_name' => '',
            'neighbor_1_relationship' => '',
            'neighbor_1_known' => '',
            'neighbor_1_address' => '',
            'neighbor_2_name' => '',
            'neighbor_2_relationship' => '',
            'neighbor_2_known' => '',
            'neighbor_2_address' => '',
            'neighbor_3_name' => '',
            'neighbor_3_relationship' => '',
            'neighbor_3_known' => '',
            'neighbor_3_address' => '',
            'main_informant_name' => '',
            'main_informant_relationship' => '',
            'main_informant_address' => '',
            'informants' => '',
            'main_informant' => '',
            'field_investigator' => 'CI User',
            'requesting_officer' => '',
            'submitted_date' => date('Y-m-d'),
            'submitted_time' => date('h:i A'),
            'date_time_inspected' => '',
            'raw_notes' => '',
        ];
    }

    public static function normalizeLabel(string $value): string
    {
        $value = html_entity_decode($value, ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $value = strtoupper($value);
        $value = preg_replace('/[^A-Z0-9]+/', ' ', $value) ?? '';

        return trim(preg_replace('/\s+/', ' ', $value) ?? '');
    }

    public static function compact(string $value): string
    {
        return trim((string) preg_replace('/\s+/', ' ', str_replace(["\r", "\n"], ' ', $value)));
    }

    public static function joinName(string $lastName, string $firstName, string $middleName): string
    {
        $lastName = self::compact($lastName);
        $firstName = self::compact($firstName);
        $middleName = self::compact($middleName);
        $firstPart = trim($firstName . ' ' . $middleName);

        if ($lastName !== '' && $firstPart !== '') {
            return $lastName . ', ' . $firstPart;
        }

        return trim($lastName . ' ' . $firstPart);
    }

    public static function parseCiNotes(string $notes): array
    {
        $record = self::defaults();
        $notes = html_entity_decode($notes, ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $record['raw_notes'] = trim($notes);

        $directMap = [
            'ACCOUNT NAME' => 'account_name',
            'PURPOSE OF LOAN' => 'purpose_of_loan',
            'GIVEN ADDRESS' => 'given_address',
            'VERIFIED ADDRESS' => 'verified_address',
            'COMPLETE ADDRESS' => 'complete_address',
            'PRESENT ADDRESS' => 'present_address',
            'PREVIOUS ADDRESS' => 'previous_address',
            'PREVIOUS' => 'previous_address',
            'PROVINCE' => 'province',
            'CONTACT NUMBER TELEPHONE NUMBER' => 'contact_number',
            'CONTACT NUMBER' => 'contact_number',
            'LENGTH OF STAY' => 'length_of_stay',
            'OWNERSHIP' => 'ownership',
            'NAME OF LANDLORD' => 'landlord_name',
            'RENTAL FEE' => 'rental_fee',
            'UNIT YEAR MODEL' => 'vehicle_unit_year_model',
            'OWNED OR MORTGAGE' => 'vehicle_owned_or_mortgage',
            'CONDITION' => 'vehicle_condition',
            'MONTHLY AMORTIZATION IF MORTGAGED' => 'vehicle_monthly_amortization',
            'TYPE OF RESIDENCE' => 'type_of_residence',
            'NO OF STOREY' => 'no_of_storey',
            'CLASSIFICATION' => 'classification',
            'MADE' => 'made_of',
            'APPEARANCE' => 'appearance',
            'ACCESSIBILITY' => 'accessibility',
            'NEIGHBORHOOD' => 'neighborhood',
            'HOUSE COLOR' => 'house_color',
            'GATE COLOR' => 'gate_color',
            'FENCE COLOR' => 'fence_color',
            'INTERIOR' => 'interior',
            'EXTERIOR' => 'exterior',
            'LOT AREA' => 'lot_area',
            'FLOOR AREA' => 'floor_area',
            'LANDMARK AND METERS AWAY' => 'landmark',
            'NEAREST CORNER' => 'corner',
            'IF WITH SECURITY GUARD AND HOA OFFICE' => 'security_guard_hoa',
            'TIME OF VISIT' => 'time_of_visit',
            'LIVING CONDITION' => 'living_condition',
            'CI REMARKS AND OBSERVATION' => 'ci_remarks_observation',
        ];

        $personMap = [
            'LAST NAME' => 'last_name',
            'FIRST NAME' => 'first_name',
            'MIDDLE NAME' => 'middle_name',
            'BDAY AGE' => 'bday_age',
            'BIRTHPLACE' => 'birthplace',
            'CIVIL STATUS' => 'civil_status',
            'NATIONALITY' => 'nationality',
            'EDUCATION ATTAINMENT' => 'education',
            'EDUCATIONAL ATTAINMENT' => 'education',
        ];

        $currentPerson = 'subject';
        $currentSection = '';
        $bufferKey = '';
        $bufferLines = [];
        $neighborIndex = 0;

        $commitBuffer = function () use (&$record, &$bufferKey, &$bufferLines, &$currentSection): void {
            if ($bufferKey === '') {
                return;
            }
            $value = trim(implode("\n", array_filter($bufferLines, static fn ($line): bool => trim((string) $line) !== '')));
            if ($value !== '') {
                if (in_array($bufferKey, ['remarks', 'informants', 'main_informant', 'dependents'], true) && $record[$bufferKey] !== '') {
                    $record[$bufferKey] .= "\n" . $value;
                } else {
                    $record[$bufferKey] = $value;
                }
            }
            $bufferKey = '';
            $bufferLines = [];
            $currentSection = '';
        };

        foreach (preg_split('/\r\n|\r|\n/', $notes) ?: [] as $rawLine) {
            $line = trim((string) $rawLine);
            if ($line === '') {
                continue;
            }

            $normalizedLine = self::normalizeLabel(rtrim($line, ':'));
            if (in_array($normalizedLine, ['NAME OF SUBJECT', 'NAME OF SPOUSE LIVE IN PARTNER'], true)) {
                $commitBuffer();
                $currentPerson = $normalizedLine === 'NAME OF SUBJECT' ? 'subject' : 'spouse';
                continue;
            }

            if (in_array($normalizedLine, ['SOURCES OF INCOME OF SUBJECT', 'SOURCES OF INCOME'], true)) {
                $commitBuffer();
                $currentSection = $currentPerson . '_income';
                continue;
            }

            if ($normalizedLine === 'SOURCES OF INCOME OF SPOUSE') {
                $commitBuffer();
                $currentSection = 'spouse_income';
                continue;
            }

            if (str_starts_with($normalizedLine, 'DEPENDENTS AGE SCHOOL')) {
                $commitBuffer();
                $bufferKey = 'dependents';
                $bufferLines = [];
                continue;
            }

            if ($normalizedLine === 'INFORMANTS') {
                $commitBuffer();
                $bufferKey = 'informants';
                $bufferLines = [];
                continue;
            }

            if (str_starts_with($normalizedLine, 'MAIN INFORMANT')) {
                $commitBuffer();
                if (str_contains($normalizedLine, 'NAME')) {
                    $record['main_informant_name'] = trim((string) preg_replace('/^[^:]*:/', '', $line));
                    $bufferKey = 'main_informant';
                    $bufferLines = [$record['main_informant_name']];
                } else {
                    $bufferKey = 'main_informant';
                    $bufferLines = [];
                }
                continue;
            }

            if (str_starts_with($normalizedLine, 'REMARKS')) {
                $commitBuffer();
                $value = trim((string) preg_replace('/^[^:]*:/', '', $line));
                $bufferKey = 'remarks';
                $bufferLines = $value !== '' ? [$value] : [];
                continue;
            }

            if ($normalizedLine === 'BANK TEMPLATE PDRN RESIDENCE VERIFICATION REPORT' || $normalizedLine === 'INFORMANTS REMARKS') {
                $commitBuffer();
                continue;
            }

            if (!str_contains($line, ':')) {
                if ($bufferKey !== '') {
                    $bufferLines[] = $line;
                }
                continue;
            }

            [$label, $value] = array_map('trim', explode(':', $line, 2));
            $normalizedLabel = self::normalizeLabel($label);

            if (isset($personMap[$normalizedLabel])) {
                $record[$currentPerson . '_' . $personMap[$normalizedLabel]] = $value;
                continue;
            }

            if ($currentSection === 'subject_income') {
                if ($normalizedLabel === 'EMPLOYER NAME') {
                    $record['subject_employer_name'] = $value;
                    $record['subject_employment'] = $value;
                    continue;
                }
                if ($normalizedLabel === 'BUSINESS NAME') {
                    $record['subject_business_name'] = $value;
                    $record['subject_business'] = $value;
                    continue;
                }
                if ($normalizedLabel === 'ADDRESS') {
                    if ($record['subject_business_name'] !== '') {
                        $record['subject_business_address'] = $value;
                    } else {
                        $record['subject_employer_address'] = $value;
                    }
                    continue;
                }
            }

            if ($currentSection === 'spouse_income') {
                if ($normalizedLabel === 'EMPLOYER NAME') {
                    $record['spouse_employer_name'] = $value;
                    $record['spouse_employment'] = $value;
                    continue;
                }
                if ($normalizedLabel === 'BUSINESS NAME') {
                    $record['spouse_business_name'] = $value;
                    $record['spouse_business'] = $value;
                    continue;
                }
            }

            if (str_starts_with($normalizedLabel, 'BARANGAY INFORMANT S NAME')) {
                $record['barangay_informant_name'] = $value;
                continue;
            }
            if ($normalizedLabel === 'POSITION' && $record['barangay_informant_name'] !== '' && $record['barangay_informant_position'] === '') {
                $record['barangay_informant_position'] = $value;
                continue;
            }
            if ($normalizedLabel === 'BARANGAY ADDRESS') {
                $record['barangay_informant_address'] = $value;
                continue;
            }
            if ($normalizedLabel === 'IF SUBJECT COMAKER IS KNOWN OR UNKNOWN' && $record['barangay_informant_name'] !== '' && $record['barangay_subject_known'] === '') {
                $record['barangay_subject_known'] = $value;
                continue;
            }

            if (str_contains($normalizedLabel, 'NEIGHBOR') && str_contains($normalizedLabel, 'NAME')) {
                $neighborIndex = min($neighborIndex + 1, 3);
                $record['neighbor_' . $neighborIndex . '_name'] = $value;
                continue;
            }
            if ($neighborIndex > 0 && $normalizedLabel === 'RELATION TO SUBJECT COMAKER') {
                $record['neighbor_' . $neighborIndex . '_relationship'] = $value;
                continue;
            }
            if ($neighborIndex > 0 && $normalizedLabel === 'IF SUBJECT COMAKER IS KNOWN OR UNKNOWN') {
                $record['neighbor_' . $neighborIndex . '_known'] = $value;
                continue;
            }
            if ($neighborIndex > 0 && $normalizedLabel === 'ADDRESS') {
                $record['neighbor_' . $neighborIndex . '_address'] = $value;
                continue;
            }

            if ($normalizedLabel === 'ADDRESS' && $record['main_informant_name'] !== '' && $record['main_informant_address'] === '') {
                $record['main_informant_address'] = $value;
                continue;
            }
            if ($normalizedLabel === 'RELATION TO SUBJECT') {
                $record['main_informant_relationship'] = $value;
                continue;
            }

            if (isset($directMap[$normalizedLabel])) {
                $record[$directMap[$normalizedLabel]] = $value;
            }
        }

        $commitBuffer();

        if ($record['complete_address'] === '') {
            $record['complete_address'] = $record['verified_address'] !== '' ? $record['verified_address'] : $record['given_address'];
        }
        if ($record['present_address'] === '') {
            $record['present_address'] = $record['verified_address'] !== '' ? $record['verified_address'] : $record['given_address'];
        }
        if ($record['remarks'] === '' && $record['ci_remarks_observation'] !== '') {
            $record['remarks'] = $record['ci_remarks_observation'];
        }
        if ($record['informants'] === '') {
            $record['informants'] = self::buildInformantsSummary($record);
        }
        if ($record['main_informant'] === '') {
            $parts = array_filter([$record['main_informant_name'], $record['main_informant_relationship'], $record['main_informant_address']]);
            $record['main_informant'] = implode("\n", $parts);
        }
        if ($record['date_time_inspected'] === '') {
            $record['date_time_inspected'] = trim($record['submitted_date'] . ' ' . $record['time_of_visit']);
        }

        return $record;
    }

    public static function buildExportPayload(array $record): array
    {
        $payload = $record;
        $payload['applicant_name'] = self::joinName($record['subject_last_name'] ?? '', $record['subject_first_name'] ?? '', $record['subject_middle_name'] ?? '');
        $payload['spouse_name'] = self::joinName($record['spouse_last_name'] ?? '', $record['spouse_first_name'] ?? '', $record['spouse_middle_name'] ?? '');
        $payload['subject_income'] = implode(' / ', array_filter([$record['subject_employment'] ?? '', $record['subject_business'] ?? '']));
        $payload['spouse_income'] = implode(' / ', array_filter([$record['spouse_employment'] ?? '', $record['spouse_business'] ?? '']));
        $payload['date_time_submitted'] = trim(($record['submitted_date'] ?? '') . ' ' . ($record['submitted_time'] ?? ''));
        $payload['request_reference'] = $record['reference_number'] ?? ($record['account_name'] ?? '');
        $payload['dependent_rows'] = self::parseDependentRows($record['dependents'] ?? '');
        $payload['dependents_count'] = (string) count($payload['dependent_rows']);
        $payload['maybank_address_parts'] = self::splitMaybankAddress(
            $record['verified_address'] ?: ($record['complete_address'] ?: ($record['given_address'] ?? ''))
        );
        $payload['residence_description'] = implode(' | ', array_filter([
            $record['type_of_residence'] ?? '',
            $record['no_of_storey'] ?? '',
            $record['classification'] ?? '',
            $record['made_of'] ?? '',
        ]));
        $payload['general_appearance'] = implode(' | ', array_filter([
            $record['appearance'] ?? '',
            $record['house_color'] ?? '',
            $record['gate_color'] ?? '',
            $record['fence_color'] ?? '',
            $record['exterior'] ?? '',
        ]));
        $payload['neighborhood_classification'] = str_contains(strtolower((string) ($record['neighborhood'] ?? '')), 'residential')
            ? 'Residential'
            : 'Others';
        $payload['adverse_finding'] = 'No Adverse Findings';
        $payload['utility_bills'] = 'None';
        $payload['outcome'] = str_contains(strtolower((string) ($record['remarks'] ?? '')), 'confirm') ? 'VERIFIED' : 'PARTIALLY VERIFIED';
        $payload['maybank_informants'] = self::buildMaybankInformants($record);
        $payload['vehicle_details'] = self::splitVehicleUnitYearModel($record['vehicle_unit_year_model'] ?? '');

        return $payload;
    }

    public static function parseDependentRows(string $value): array
    {
        $rows = [];
        foreach (preg_split('/\r\n|\r|\n/', $value) ?: [] as $line) {
            $line = trim((string) preg_replace('/^\d+[\.\)]?\s*/', '', trim((string) $line)));
            if ($line === '' || self::normalizeLabel($line) === 'NONE') {
                continue;
            }
            $parts = array_map([self::class, 'compact'], explode('/', $line));
            $rows[] = [
                'name' => $parts[0] ?? '',
                'age' => $parts[1] ?? '',
                'school' => $parts[2] ?? '',
                'grade' => $parts[3] ?? '',
                'course' => $parts[4] ?? '',
            ];
        }

        return array_slice($rows, 0, 3);
    }

    public static function splitMaybankAddress(string $address): array
    {
        $result = [
            'unit_building' => '',
            'street' => '',
            'village_subdivision' => '',
            'barangay' => '',
            'city' => '',
            'province' => '',
            'region' => '',
        ];

        $parts = array_values(array_filter(array_map([self::class, 'compact'], explode(',', $address))));
        if ($parts === []) {
            return $result;
        }

        if (preg_match('/^([0-9A-Z\-\/]+)\s+(.+)$/i', $parts[0], $matches)) {
            $result['unit_building'] = self::compact($matches[1]);
            $result['street'] = self::compact($matches[2]);
        } else {
            $result['street'] = $parts[0];
        }

        foreach (array_slice($parts, 1) as $part) {
            $normalized = self::normalizeLabel($part);
            if (str_contains($normalized, 'BRGY') || str_contains($normalized, 'BARANGAY')) {
                $result['barangay'] = $part;
            } elseif (str_contains($normalized, 'CITY') || str_contains($normalized, 'MUNICIPALITY')) {
                $result['city'] = $part;
            } elseif ($result['village_subdivision'] === '') {
                $result['village_subdivision'] = $part;
            } else {
                $result['province'] = $part;
            }
        }

        return $result;
    }

    public static function buildInformantsSummary(array $record): string
    {
        $lines = [];
        if (($record['barangay_informant_name'] ?? '') !== '') {
            $lines[] = implode(' / ', array_filter([
                $record['barangay_informant_name'] ?? '',
                $record['barangay_informant_position'] ?? '',
                $record['barangay_subject_known'] ?? '',
                $record['barangay_informant_address'] ?? '',
            ]));
        }
        for ($i = 1; $i <= 3; $i++) {
            if (($record['neighbor_' . $i . '_name'] ?? '') === '') {
                continue;
            }
            $lines[] = implode(' / ', array_filter([
                $record['neighbor_' . $i . '_name'] ?? '',
                $record['neighbor_' . $i . '_relationship'] ?? '',
                $record['neighbor_' . $i . '_known'] ?? '',
                $record['neighbor_' . $i . '_address'] ?? '',
            ]));
        }

        return implode("\n", $lines);
    }

    public static function buildMaybankInformants(array $record): array
    {
        $rows = [];
        if (($record['barangay_informant_name'] ?? '') !== '') {
            $rows[] = [
                'name' => $record['barangay_informant_name'],
                'relationship' => implode(' / ', array_filter(['Barangay Informant', $record['barangay_informant_position'] ?? '', $record['barangay_subject_known'] ?? ''])),
            ];
        }
        for ($i = 1; $i <= 3; $i++) {
            if (($record['neighbor_' . $i . '_name'] ?? '') === '') {
                continue;
            }
            $rows[] = [
                'name' => $record['neighbor_' . $i . '_name'],
                'relationship' => implode(' / ', array_filter([$record['neighbor_' . $i . '_relationship'] ?? '', $record['neighbor_' . $i . '_known'] ?? ''])),
            ];
        }
        if (($record['main_informant_name'] ?? '') !== '') {
            $rows[] = [
                'name' => $record['main_informant_name'],
                'relationship' => implode(' / ', array_filter(['Main Informant', $record['main_informant_relationship'] ?? ''])),
            ];
        }

        return array_slice($rows, 0, 8);
    }

    public static function splitVehicleUnitYearModel(string $value): array
    {
        $value = self::compact($value);
        if ($value === '') {
            return ['make_model' => '', 'year_model' => ''];
        }
        if (preg_match('/\b((?:19|20)\d{2})\b/', $value, $matches, PREG_OFFSET_CAPTURE)) {
            $year = $matches[1][0];
            $offset = $matches[1][1];

            return [
                'make_model' => self::compact(substr($value, 0, $offset)),
                'year_model' => $year,
            ];
        }

        return ['make_model' => $value, 'year_model' => ''];
    }
}
