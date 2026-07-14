<?php

declare(strict_types=1);

namespace App;

final class GeminiClient
{
    public static function analyzeImage(
        string $apiKey,
        string $imageBytes,
        string $mimeType,
        string $companyName,
        string $officerName,
        string $inspectionContext,
        bool $strictMode
    ): array {
        if ($apiKey === '') {
            return ['error' => 'Missing GEMINI_API_KEY.'];
        }

        $strictness = $strictMode
            ? 'Be strict and conservative. Visible damage, rust, moisture, cracks, rot, corrosion, wear, or poor maintenance should lower ratings.'
            : 'Be balanced and objective. Use only visible evidence in the image.';

        $prompt = trim(
            "You are an enterprise-grade image inspection AI for {$companyName}.\n" .
            "Inspector name: " . ($officerName !== '' ? $officerName : 'Not provided') . ".\n" .
            "Inspection context: {$inspectionContext}\n\n" .
            "Analyze the uploaded image carefully and return only valid JSON with scene_type, overall_rating, overall_summary, priority_risks, overall_recommendations, and objects. " .
            "Each object must include object_name, rating, confidence, condition_summary, findings, positive_indicators, risk_indicators, and recommendations. {$strictness}"
        );

        $payload = [
            'contents' => [[
                'parts' => [
                    ['text' => $prompt],
                    [
                        'inline_data' => [
                            'mime_type' => $mimeType,
                            'data' => base64_encode($imageBytes),
                        ],
                    ],
                ],
            ]],
            'generationConfig' => [
                'temperature' => 0.2,
                'responseMimeType' => 'application/json',
            ],
        ];

        $ch = curl_init('https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=' . urlencode($apiKey));
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_SLASHES),
            CURLOPT_TIMEOUT => 90,
        ]);

        $response = curl_exec($ch);
        $httpCode = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlError = curl_error($ch);
        curl_close($ch);

        if ($response === false || $curlError !== '') {
            return ['error' => 'Unable to reach Gemini API: ' . $curlError];
        }

        $data = json_decode($response, true);
        if ($httpCode >= 400) {
            return ['error' => 'Gemini API error: ' . ((string) ($data['error']['message'] ?? 'Unknown error'))];
        }

        $text = '';
        foreach (($data['candidates'][0]['content']['parts'] ?? []) as $part) {
            $text .= (string) ($part['text'] ?? '');
        }

        $decoded = json_decode($text, true);
        if (!is_array($decoded)) {
            return ['error' => 'The AI returned an unreadable response.'];
        }

        $decoded['objects'] ??= [];
        $decoded['priority_risks'] ??= [];
        $decoded['overall_recommendations'] ??= [];

        return $decoded;
    }
}
