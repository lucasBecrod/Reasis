import '../database.dart';

class InstitucionesEducativasTable
    extends SupabaseTable<InstitucionesEducativasRow> {
  @override
  String get tableName => 'instituciones_educativas';

  @override
  InstitucionesEducativasRow createRow(Map<String, dynamic> data) =>
      InstitucionesEducativasRow(data);
}

class InstitucionesEducativasRow extends SupabaseDataRow {
  InstitucionesEducativasRow(Map<String, dynamic> data) : super(data);

  @override
  SupabaseTable get table => InstitucionesEducativasTable();

  int get id => getField<int>('id')!;
  set id(int value) => setField<int>('id', value);

  DateTime get createdAt => getField<DateTime>('created_at')!;
  set createdAt(DateTime value) => setField<DateTime>('created_at', value);

  String? get codigoModular => getField<String>('codigo_modular');
  set codigoModular(String? value) => setField<String>('codigo_modular', value);

  String? get nombreInstitucion => getField<String>('nombre_institucion');
  set nombreInstitucion(String? value) =>
      setField<String>('nombre_institucion', value);

  String? get redEducativa => getField<String>('red_educativa');
  set redEducativa(String? value) => setField<String>('red_educativa', value);
}
