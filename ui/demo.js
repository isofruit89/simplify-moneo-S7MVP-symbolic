// Browser preview only (index.html?demo). Not bundled into the exe.
const DEMO = [
 {
  "id": "83516987097c40eb9fe8dec6c55cb30b",
  "ok": true,
  "xmlPath": "C:\\Demo\\DB_Sensors.xml",
  "fileName": "DB_Sensors.xml",
  "dbName": "DB_Sensors",
  "defaultFilename": "DB_Sensors.json",
  "signals": [
   {
    "Address": "PLC.Blocks.DB_Sensors.Temperature;REAL",
    "MeasurementName": "Temperature",
    "Unit": "K",
    "Type": "FLOAT"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.Pressure;LREAL",
    "MeasurementName": "Pressure",
    "Unit": "K",
    "Type": "DOUBLE"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.Compteur_µ;DINT",
    "MeasurementName": "Compteur_µ",
    "Unit": "K",
    "Type": "INT32"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.Status;WORD",
    "MeasurementName": "Status",
    "Unit": "K",
    "Type": "UINT32"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.Enable;BOOL",
    "MeasurementName": "Enable",
    "Unit": "K",
    "Type": "BOOLEAN"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.Text;STRING",
    "MeasurementName": "Text",
    "Unit": "K",
    "Type": "STRING"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.WText;WSTRING",
    "MeasurementName": "WText",
    "Unit": "K",
    "Type": "STRING"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.BigNumber;ULINT",
    "MeasurementName": "BigNumber",
    "Unit": "K",
    "Type": "UINT64"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.Motor.Speed;INT",
    "MeasurementName": "Speed",
    "Unit": "K",
    "Type": "INT32"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.Motor.Current;REAL",
    "MeasurementName": "Current",
    "Unit": "K",
    "Type": "FLOAT"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.Motor.Bearing.Vibration;REAL",
    "MeasurementName": "Vibration",
    "Unit": "K",
    "Type": "FLOAT"
   },
   {
    "Address": "PLC.Blocks.DB_Sensors.Motor.Bearing.Ok;BOOL",
    "MeasurementName": "Ok",
    "Unit": "K",
    "Type": "BOOLEAN"
   }
  ],
  "skipped": [
   {
    "path": "Values",
    "datatype": "Array[0..3] of Int",
    "reason": "Arrays are not transferred"
   },
   {
    "path": "Runtime",
    "datatype": "Time",
    "reason": "Data type TIME is not supported"
   },
   {
    "path": "Timestamp",
    "datatype": "DTL",
    "reason": "Data type DTL is not supported"
   },
   {
    "path": "Drive",
    "datatype": "\"typeDrive\"",
    "reason": "UDT/PLC data type without resolved elements"
   },
   {
    "path": "EmptyStruct",
    "datatype": "Struct",
    "reason": "Struct without elements"
   },
   {
    "path": "NoType",
    "datatype": "",
    "reason": "Name or data type missing"
   }
  ]
 },
 {
  "id": "44dfb189ca184f8181182eb628c0733f",
  "ok": true,
  "xmlPath": "C:\\Demo\\NoName.xml",
  "fileName": "NoName.xml",
  "dbName": "UnknownDB",
  "defaultFilename": "NoName.json",
  "signals": [
   {
    "Address": "PLC.Blocks.UnknownDB.A;BYTE",
    "MeasurementName": "A",
    "Unit": "K",
    "Type": "UINT32"
   },
   {
    "Address": "PLC.Blocks.UnknownDB.B;USINT",
    "MeasurementName": "B",
    "Unit": "K",
    "Type": "UINT32"
   }
  ],
  "skipped": []
 },
 {
  "ok": false,
  "fileName": "Broken.xml",
  "xmlPath": "C:\\Demo\\Broken.xml",
  "error": "The file is not valid XML (no element found: line 1, column 41)."
 }
];

export function createDemoApi() {
  let n = 0;
  return {
    info: async () => ({ title: "TIA → moneo Converter", version: "3.0 (Demo)" }),
    pick_files: async () => DEMO.slice(n++ % 3, (n % 3) + 1).map((d) => ({ ...d })),
    remove: async () => true,
    save_one: async (id) => ({ ok: true, path: "C:\Demo\\" + DEMO.find((d) => d.id === id).defaultFilename }),
    choose_folder: async () => "C:\Demo\Export",
    save_all: async (ids, folder, overwrite) => overwrite || ids.length < 2
      ? { ok: true, saved: ids.map((i) => folder + "\\" + DEMO.find((d) => d.id === i).defaultFilename), errors: [], folder }
      : { ok: false, conflicts: ["DB_Sensoren.json"] },
    open_in_explorer: async () => true,
  };
}
