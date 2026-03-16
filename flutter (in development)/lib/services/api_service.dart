import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // ── Base URL — change this if deploying elsewhere ─────────
  static const String baseUrl = 'http://localhost';

  // ── Get current session user_id from SharedPreferences ───
  static Future<int> _getUserId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt('user_id') ?? 1;
  }

  // ── Login ─────────────────────────────────────────────────
  static Future<Map<String, dynamic>> login(
      String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/php/login.php'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'username': username, 'password': password}),
    );
    return json.decode(response.body);
  }

  // ── Get records ───────────────────────────────────────────
  static Future<List<dynamic>> getRecords({
    String? type,
    String? search,
    String? status,
  }) async {
    final params = <String, String>{};
    if (type   != null && type.isNotEmpty)   params['type']   = type;
    if (search != null && search.isNotEmpty) params['search'] = search;
    if (status != null && status.isNotEmpty) params['status'] = status;

    final uri = Uri.parse('$baseUrl/php/get_records.php')
        .replace(queryParameters: params.isNotEmpty ? params : null);
    final response = await http.get(uri);
    final data = json.decode(response.body);
    return data is List ? data : [];
  }

  // ── Update record status (Approve / Reject / Pending) ────
  static Future<Map<String, dynamic>> updateStatus(
      dynamic docId, String status) async {
    return saveRecord({}, docId: docId, status: status);
  }

  // ── Upload + process document ─────────────────────────────
  static Future<Map<String, dynamic>> uploadDocument({
    required String filePath,
    required String fileName,
    required String fileType,
    required String docType,
  }) async {
    final userId = await _getUserId();
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/php/process_upload.php'),
    );
    request.files.add(await http.MultipartFile.fromPath(
      'file',
      filePath,
      filename: fileName,
    ));
    request.fields['type']    = docType;
    request.fields['user_id'] = userId.toString();

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);
    return json.decode(response.body);
  }

  // Save record — for new records omit docId and pass type + rawText.
  // For existing records pass docId (status update / field edit).
  static Future<Map<String, dynamic>> saveRecord(
    Map<String, dynamic> formData, {
    dynamic docId,
    String? type,
    String? status,
    String? rawText,
  }) async {
    final userId = await _getUserId();
    final body = <String, dynamic>{
      'formData': formData,
      'status':   status ?? 'Pending',
      'user_id':  userId,
    };
    if (docId   != null) body['doc_id']   = docId;
    if (type    != null) body['type']     = type;
    if (rawText != null) body['raw_text'] = rawText;

    final response = await http.post(
      Uri.parse('$baseUrl/php/save_record.php'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    );
    return json.decode(response.body);
  }

  // ── Dashboard stats ───────────────────────────────────────
  static Future<Map<String, dynamic>> getDashboardStats() async {
    final response = await http.get(
      Uri.parse('$baseUrl/php/get_dashboard_stats.php'),
    );
    final data = json.decode(response.body);
    return data is Map<String, dynamic> ? data : {};
  }
}