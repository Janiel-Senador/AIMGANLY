<?php

declare(strict_types=1);

namespace App;

use PhpOffice\PhpSpreadsheet\Cell\Coordinate;
use PhpOffice\PhpSpreadsheet\IOFactory;
use PhpOffice\PhpSpreadsheet\Spreadsheet;
use PhpOffice\PhpSpreadsheet\Worksheet\Worksheet;

final class PdrnExporter
{
    public static function export(array $record, string $templateKey): array
    {
        $definitions = Config::templateDefinitions();
        $definition = $definitions[$templateKey] ?? $definitions['bpi'];
        $payload = NotesParser::buildExportPayload($record);

        $spreadsheet = IOFactory::load($definition['path']);
        $sheet = $spreadsheet->getSheetByName($definition['sheet_name']) ?? $spreadsheet->getActiveSheet();

        if ($templateKey === 'maybank') {
            self::fillMaybankTemplate($sheet, $payload);
        } else {
            self::fillBpiTemplate($sheet, $payload);
        }

        $writer = IOFactory::createWriter($spreadsheet, 'Xlsx');
        $filename = sprintf(
            '%s_%s_pdrn_output.xlsx',
            $templateKey,
            trim((string) preg_replace('/[^A-Za-z0-9]+/', '_', (string) ($record['subject_last_name'] ?? 'record')), '_') ?: 'record'
        );
        $path = Config::exportPath() . DIRECTORY_SEPARATOR . $filename;
        $writer->save($path);

        return [$path, $filename];
    }

    private static function setValue(Worksheet $sheet, string $cellRef, mixed $value): void
    {
        $target = $cellRef;
        foreach ($sheet->getMergeCells() as $mergedRange) {
            if (!Coordinate::coordinateIsInsideRange($cellRef, $mergedRange)) {
                continue;
            }
            [$target] = Coordinate::splitRange($mergedRange)[0];
            break;
        }

        $sheet->setCellValue($target, $value ?? '');
    }

    private static function fillBpiTemplate(Worksheet $sheet, array $payload): void
    {
        $map = [
            'P4' => $payload['bpi_request_number'] ?? '',
            'P5' => $payload['los_request_number'] ?? '',
            'M8' => $payload['applicant_name'] ?? '',
            'M9' => $payload['subject_civil_status'] ?? '',
            'M10' => $payload['spouse_name'] ?? '',
            'M11' => $payload['dependents_count'] ?? '',
            'AA20' => $payload['present_address'] ?? '',
            'U25' => $payload['length_of_stay'] ?? '',
            'U26' => $payload['ownership'] ?? '',
            'AW36' => $payload['time_of_visit'] ?? '',
            'B39' => $payload['remarks'] ?? '',
            'T56' => $payload['field_investigator'] ?? '',
        ];

        foreach ($map as $cell => $value) {
            self::setValue($sheet, $cell, $value);
        }
    }

    private static function fillMaybankTemplate(Worksheet $sheet, array $payload): void
    {
        $address = $payload['maybank_address_parts'] ?? [];
        $vehicle = $payload['vehicle_details'] ?? [];
        $dependents = $payload['dependent_rows'] ?? [];
        $map = [
            'J10' => $payload['request_reference'] ?? '',
            'AB10' => $payload['date_time_inspected'] ?? '',
            'J12' => $payload['requesting_officer'] ?? '',
            'AB12' => $payload['date_time_submitted'] ?? '',
            'F16' => $payload['applicant_name'] ?? '',
            'Q16' => $payload['subject_bday_age'] ?? '',
            'V16' => $payload['subject_education'] ?? '',
            'AG16' => $payload['subject_income'] ?? '',
            'F18' => $payload['subject_civil_status'] ?? '',
            'V18' => $payload['subject_nationality'] ?? '',
            'AG18' => $payload['dependents_count'] ?? '',
            'F20' => $payload['spouse_name'] ?? '',
            'Q20' => $payload['spouse_bday_age'] ?? '',
            'V20' => $payload['spouse_education'] ?? '',
            'AG20' => $payload['spouse_income'] ?? '',
            'F22' => $payload['spouse_civil_status'] ?? '',
            'V22' => $payload['spouse_nationality'] ?? '',
            'B25' => $dependents[0]['name'] ?? '',
            'J25' => $dependents[0]['age'] ?? '',
            'O25' => $dependents[0]['school'] ?? '',
            'Y25' => $dependents[0]['grade'] ?? '',
            'B26' => $dependents[1]['name'] ?? '',
            'J26' => $dependents[1]['age'] ?? '',
            'O26' => $dependents[1]['school'] ?? '',
            'Y26' => $dependents[1]['grade'] ?? '',
            'B29' => $address['unit_building'] ?? '',
            'H29' => $address['street'] ?? '',
            'N29' => $address['village_subdivision'] ?? '',
            'T29' => $address['barangay'] ?? '',
            'Y29' => $address['city'] ?? '',
            'AE29' => $address['province'] ?? '',
            'AJ29' => $address['region'] ?? '',
            'L32' => $payload['present_address'] ?? '',
            'B35' => $payload['ownership'] ?? '',
            'AD36' => $payload['landlord_name'] ?? '',
            'AD37' => $payload['rental_fee'] ?? '',
            'AD38' => $payload['outcome'] ?? '',
            'E44' => $payload['length_of_stay'] ?? '',
            'B47' => $payload['residence_description'] ?? '',
            'W47' => $payload['contact_number'] ?? '',
            'AF47' => $payload['subject_income'] ?? '',
            'P49' => $payload['lot_area'] ?? '',
            'P50' => $payload['floor_area'] ?? '',
            'B56' => $payload['general_appearance'] ?? '',
            'B59' => $payload['utility_bills'] ?? '',
            'K59' => $payload['adverse_finding'] ?? '',
            'W59' => $payload['neighborhood_classification'] ?? '',
            'B65' => $payload['neighborhood'] ?? '',
            'P65' => $payload['accessibility'] ?? '',
            'W66' => $payload['landmark'] ?? '',
            'W67' => $payload['corner'] ?? '',
            'W68' => $payload['time_of_visit'] ?? '',
            'W69' => $payload['security_guard_hoa'] ?? '',
            'B74' => $vehicle['make_model'] ?? '',
            'L74' => $vehicle['year_model'] ?? '',
            'Q74' => $payload['vehicle_owned_or_mortgage'] ?? '',
            'AC74' => $payload['vehicle_monthly_amortization'] ?? '',
            'B79' => $payload['ci_remarks_observation'] ?? ($payload['remarks'] ?? ''),
            'B103' => $payload['field_investigator'] ?? '',
            'T103' => $payload['requesting_officer'] ?? '',
        ];

        foreach ($map as $cell => $value) {
            self::setValue($sheet, $cell, $value);
        }

        $informants = $payload['maybank_informants'] ?? [];
        foreach ([91, 92, 93, 94, 95, 96, 97, 98] as $index => $row) {
            self::setValue($sheet, 'B' . $row, $informants[$index]['name'] ?? '');
            self::setValue($sheet, 'T' . $row, $informants[$index]['relationship'] ?? '');
        }
    }
}
